# -*- coding: utf-8 -*-

from __future__ import unicode_literals, print_function, division

import random
#import pdb

import torch
import torch.nn as nn
from torch.autograd import Variable
import torch.nn.functional as F
import torch.optim as optim

import string
import unicodedata
import glob
from io import open

from tornado import gen

from multiprocessing import Process
import pickle
import redis

isCUDA = torch.cuda.is_available()
EPOCH = 2

def processTrainData(datas):
    mapdict = { c:i for i, c in enumerate(string.printable)}
    oc  = len(string.printable) + 1
    trainData = []
    for v, l in datas:
        if isCUDA:
            trainData.append((torch.LongTensor([mapdict.get(ic, oc) for ic in v]).cuda(), torch.LongTensor([l]).cuda()))
        else:
            trainData.append((torch.LongTensor([mapdict.get(ic, oc) for ic in v]), torch.LongTensor([l])))
    return trainData



class RNN(nn.Module):
    def __init__(self, vocab_size, embedding_dim, hidden_dim, n_categories):
        super(RNN, self).__init__()
        self.hidden_dim = hidden_dim
        self.embeddings = nn.Embedding(vocab_size, embedding_dim)
        self.lstm = nn.LSTM(embedding_dim, self.hidden_dim, 1)

        self.linear1 = nn.Linear(self.hidden_dim, n_categories)
        self.softmax = nn.LogSoftmax()

    def forward(self, input, hidden):
        # pdb.set_trace()
        embeds = self.embeddings(input).unsqueeze(dim=0).permute(1, 0, 2)
        # print(embeds.shape, hidden.shape)
        output, hidden = self.lstm(embeds, hidden)
        output = F.relu(self.linear1(output[-1]))
        return output, hidden

    def initHidden(self, length=1):
        if isCUDA:
            return (Variable(torch.zeros(1, length, self.hidden_dim).cuda()),
                    Variable(torch.zeros(1, length, self.hidden_dim).cuda()))
        else:
            return (Variable(torch.zeros(1, length, self.hidden_dim)),
                    Variable(torch.zeros(1, length, self.hidden_dim)))

def trainLocalModel(epoch, traindatas):
    n_categories = 2
    n_hidden = 20
    embedding_dim = 16
    n_letters = len(string.printable) + 2

    model = RNN(n_letters, embedding_dim, n_hidden, n_categories)
    if isCUDA:
        model.cuda()
    optimizer = optim.SGD(model.parameters(), lr=0.01, momentum=0.5)
    criterion = nn.CrossEntropyLoss()
    model.train()
    length = len(traindatas)
    for i in range(epoch):
        hidden = model.initHidden()
        total_error = 0
        for idx, (tensor, label) in enumerate(traindatas):
            model.zero_grad()
            loss = 0
            feature = Variable(tensor)
            output, _ = model(feature, hidden)
            loss += criterion(output, Variable(label))  # Variable())
            loss.backward()
            optimizer.step()
            if idx % 2000 == 0:
                print('batch error %f' % loss.data[0])
            total_error += loss.data[0]
        print('epoch error %f' % (total_error/length))
    return  model


def _trainModel(config, key, datas):
    global EPOCH
    r = redis.Redis(host=config['host'],
                    port=config['port'],
                    #password=config['passwd'],
                    decode_responses=True)
    key_status = key + '_status'
    status = r.get(key_status)
    if status is None:
        r.set(key_status, 'training')
        traindata = processTrainData(datas)
        model = trainLocalModel(EPOCH, traindata)
        r.set(key, pickle.dumps(model))
        r.delete(key_status)


def trainModel(config, key, datas):
    #创建进程，然后训练模型，放到redis里
    p = Process(target=_trainModel, args=(config['redis'], key,  datas))
    p.daemon = True
    p.start()

_rnn_localsmodel = {}

@gen.coroutine
def getModel(client, key):
    model = _rnn_localsmodel.get(key, None)
    if model:
        return model
    # model = yield Task(client.get, key)
    model = yield client.get(key)
    if model:
        model = pickle.loads(model)
        # 需要反序列化
        _rnn_localsmodel[key] = model #pickle.loads(model)
        return model

def estimate(model, sequence):
    if isCUDA:
        model.cuda()
    model.eval()
    model.zero_grad()
    mapdict = {c: i for i, c in enumerate(string.printable)}
    oc = len(string.printable) + 1
    if isCUDA:
        sequence = torch.LongTensor([mapdict.get(ic, oc) for ic in sequence]).cuda()
    else:
        sequence = torch.LongTensor([mapdict.get(ic, oc) for ic in sequence])
    hidden = model.initHidden()
    feature = Variable(sequence)
    output, _ = model(feature, hidden)
    _, index = output.topk(1)
    if int(index.data[0, 0]) == 1:
        return True
    return False