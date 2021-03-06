from __future__ import print_function, division
import shutil
import torch
import torch.nn as nn
import torch.optim as optim
from torch.optim import lr_scheduler
from torch.autograd import Variable
import numpy as np
import torchvision
from torchvision import datasets, models, transforms
import matplotlib.pyplot as plt
import time
import os
import torch.utils.data as data
import torch.nn.functional as F
from config import GTEA as DATA
from utils.folder import SequencePreloader, NpySequencePreloader

DEVICE = 1

#Data statistics
mean = DATA.rgb['mean']
std = DATA.rgb['std']
num_classes = DATA.rgb_lstm['num_classes']
class_map = DATA.rgb_lstm['class_map']

#Training parameters
lr = DATA.rgb_lstm['lr']
momentum = DATA.rgb_lstm['momentum']
step_size = DATA.rgb_lstm['step_size']
gamma = DATA.rgb_lstm['gamma']
num_epochs = DATA.rgb_lstm['num_epochs']
batch_size = DATA.rgb_lstm['batch_size']
sequence_length = DATA.rgb_lstm['sequence_length']
data_transforms= DATA.rgb_lstm['data_transforms']

#Directory names
data_dir = DATA.rgb['data_dir']
png_dir = DATA.rgb['png_dir']
weights_dir = DATA.rgb['weights_dir']
features_2048_dir = DATA.rgb_lstm['features_2048_dir']

#csv files
train_csv = DATA.rgb_lstm['train_csv']
test_csv = DATA.rgb_lstm['test_csv']

class ResNet50Bottom(nn.Module):
    """
        Model definition.
    """
    def __init__(self, original_model):
        super(ResNet50Bottom, self).__init__()
        self.features = nn.Sequential(*list(original_model.children())[:-2])
        self.avg_pool = nn.AvgPool2d(10,1)

    def forward(self, x):
        x = x.view(-1, 3, 300, 300)
        x = self.features(x)
        x = self.avg_pool(x)
        x = x.view(-1, 2048)
        return x

class LSTMNet(nn.Module):
    def __init__(self, input_size, hidden_size):
        super(LSTMNet, self).__init__()
        self.hidden_size = hidden_size
        self.rnn = nn.LSTM(input_size, hidden_size, 1, batch_first=True)
        self.out = nn.Linear(hidden_size, num_classes)

    def forward(self, inp):
        x = self.rnn(inp)[0]
        outputs = self.out(x)

        outputs_mean = Variable(torch.zeros(outputs.size()[0], num_classes)).cuda(DEVICE)
        for i in range(outputs.size()[0]):
            outputs_mean[i] = outputs[i].mean(dim=0)

        return outputs_mean

class Net(nn.Module):
    def __init__(self, model_conv, input_size, hidden_size):
        super(Net, self).__init__()
        self.resnet50Bottom = ResNet50Bottom(model_conv)
        self.lstmNet = LSTMNet(input_size, hidden_size)

    def forward(self, inp, phase):
        if phase == 'train':
            features = []

            batch_size = inp.size()[0]
            sequence_length = inp.size()[1]

            inp = inp.view(-1, 3, 300, 300)
            for i in range(0, inp.size()[0], 128):
                features.append(self.resnet50Bottom(inp[i:i+128]))

            feature_sequence = torch.cat(features, dim=0)
            feature_sequence = feature_sequence.view(batch_size, sequence_length, 2048)
            outputs = self.lstmNet(feature_sequence)
            return outputs
        else:
            outputs = self.lstmNet(inp)
            return outputs

def train_model(model, criterion, optimizer, scheduler, num_epochs=2000):
    """
        Training model with given criterion, optimizer for num_epochs.
    """
    since = time.time()

    best_model_wts = model.state_dict()
    best_acc = 0.0

    train_loss = []
    train_acc = []
    test_acc = []
    test_loss = []


    for epoch in range(0,num_epochs):

        print('Epoch {}/{}'.format(epoch, num_epochs - 1))
        print('-' * 10)

        for phase in ['train', 'test']:
            if phase == 'train':
                scheduler.step()
                model.train(True)  # Set model to training mode
            else:
                model.train(False)  # Set model to etestuate mode

            running_loss = 0.0
            running_corrects = 0

            for data in dataloaders[phase]:
                inputs, labels = data

                inputs = Variable(inputs.cuda(DEVICE))
                labels = Variable(labels.cuda(DEVICE))
        
                optimizer.zero_grad()
                outputs = model(inputs, phase)
                _, preds = torch.max(outputs.data, 1)
                loss = criterion(outputs, labels)

                if phase == 'train':
                    loss.backward()
                    optimizer.step()

                running_loss += loss.data[0]
                running_corrects += torch.sum(preds == labels.data)[0].cpu().numpy()

            epoch_loss = running_loss / (dataset_sizes[phase] * 1.0)
            epoch_acc = running_corrects / (dataset_sizes[phase] * 1.0)

            if phase=='train':
                train_loss.append(epoch_loss)
                train_acc.append(epoch_acc)
                print ('##############################################################')
                print ("{} loss = {}, acc = {},".format(phase, epoch_loss, epoch_acc))
            else:
                test_loss.append(epoch_loss)
                test_acc.append(epoch_acc)
                print (" {} loss = {}, acc = {},".format(phase, epoch_loss, epoch_acc))
                print ('##############################################################')


            if phase == 'test' and epoch_acc > best_acc:
                best_acc = epoch_acc
                print ('saving model.....')
                torch.save(model,weights_dir + 'weights_'+ file_name + '_lr_' + str(lr) + '_momentum_' + str(momentum) + '_step_size_' + \
                        str(step_size) + '_gamma_' + str(gamma) + '_seq_length_' + str(sequence_length) + '_num_classes_' + str(num_classes) + \
                        '_batch_size_' + str(batch_size) + '.pt')
        print()

    time_elapsed = time.time() - sinceview(1,-1)
    print('Training complete in {:.0f}m {:.0f}s'.format(
        time_elapsed // 60, time_elapsed % 60))
    print('Best test Acc: {:4f}'.format(best_acc))

    model = torch.load(weights_dir + 'weights_'+ file_name + '_lr_' + str(lr) + '_momentum_' + str(momentum) + '_step_size_' + \
                        str(step_size) + '_gamma_' + str(gamma) + '_seq_length_' + str(sequence_length) + '_num_classes_' + str(num_classes) + \
                        '_batch_size_' + str(batch_size) + '.pt')

    return model

#Dataload and generator initialization
sequence_datasets = {'train': SequencePreloader(data_dir + png_dir, data_dir + train_csv, mean, std, [280, 450], [224, 224], 300), \
                    'test': NpySequencePreloader(data_dir + features_2048_dir, data_dir + test_csv)}

dataloaders = {x: torch.utils.data.DataLoader(sequence_datasets[x], batch_size=batch_size, shuffle=True, num_workers=6) for x in ['train', 'test']}
dataset_sizes = {x: len(sequence_datasets[x]) for x in ['train', 'test']}


file_name = __file__.split('/')[-1].split('.')[0]

model_conv = torch.load(weights_dir + 'weights_rgb_cnn_lr_0.001_momentum_0.9_step_size_15_gamma_1_num_classes_10_batch_size_128.pt')
#print(model_conv)
for param in model_conv.parameters():
    param.requires_grad = False

hidden_size = 512
input_size = 2048
model = Net(model_conv, input_size, hidden_size)
#print (model)
model = model.cuda(DEVICE)
criterion = nn.CrossEntropyLoss()
optimizer = optim.SGD(model.lstmNet.parameters(), lr=lr, momentum=momentum)
exp_lr_scheduler = lr_scheduler.StepLR(optimizer, step_size=step_size, gamma=gamma)
model = train_model(model, criterion, optimizer, exp_lr_scheduler, num_epochs=num_epochs)
