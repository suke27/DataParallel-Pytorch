import torch
import os
from torch.autograd import Variable
import argparse
import torchvision
import torchvision.transforms as transforms
import torch.optim as optim
import torch.nn as nn
from datetime import datetime
import pickle
import time

import utils.cnn_model as cnn_model
from torchvision import transforms, datasets

parser = argparse.ArgumentParser(description='CIFAR-10 classification demo')

parser.add_argument('--epochs', default=100, type=int,
        help='manual epoch number (default: 100)')
parser.add_argument('--batch-size', default=256, type=int,
        help='batch size (default: 256)')
parser.add_argument('--gpu', default='3', type=str,
        help='selected gpu (default: 3)')
parser.add_argument('--model-name', default='alexnet', type=str,
        help='model name (default: alexnet)')
parser.add_argument('--pretrained', default=False, type=bool,
        help='use pretrained model or not')

def data_loader(model_name, data_dir='./data/CIFAR-10/'):
    if model_name == "alexnet":
        transform = transforms.Compose([
            transforms.Scale(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])])
    if model_name == "base-model":
        transform = transforms.Compose([
            transforms.ToTensor(),
            transforms.Normalize([0.5, 0.5, 0.5], [0.5, 0.5, 0.5])])
    # trainset = datasets.ImageFolder(os.path.join(data_dir, 'train-image'),
    #         transform)
    # testset = datasets.ImageFolder(os.path.join(data_dir, 'test-image'),
    #         transform)
    trainset = torchvision.datasets.CIFAR10(root='./data', train=True,
                                            download=True, transform=transform)


    testset = torchvision.datasets.CIFAR10(root='./data', train=False,
                                           download=True, transform=transform)

    trainloader = torch.utils.data.DataLoader(
                trainset, batch_size=args.batch_size,shuffle=True,num_workers=4)
    testloader = torch.utils.data.DataLoader(
            testset, batch_size=args.batch_size,shuffle=False,num_workers=4)
    return trainloader, testloader
        
def train(trainloader, model, criterion, optimizer):
    model.train()
    
    train_loss = 0.0
    train_acc = 0.0
    total = 0.0

    for i, (inputs, labels) in enumerate(trainloader):
        batch_time = time.time()
        inputs, labels = inputs.cuda(), labels.cuda()
        inputs_var, labels_var = Variable(inputs), Variable(labels)

        model.zero_grad()
        
        outputs = model(inputs_var)
        loss = criterion(outputs, labels_var)
        loss.backward()
        optimizer.step()
        batch_time = time.time() - batch_time

        _, pred = torch.max(outputs.data, 1)
        total += labels.size(0)
        train_loss += loss.data[0]
        acc = (pred == labels).sum()
        train_acc += acc
        # print('[Batch: %d/%d][Loss: %3.3f][Acc: %3.3f][Batch Time: %3.3f]' % \
        #       (i, len(trainloader), loss.data[0], acc / labels.size(0),  batch_time))

    train_loss = train_loss / len(trainloader)
    train_acc = train_acc / total
    return train_loss, train_acc 

def test(testloader, model, criterion):
    model.eval()
    
    test_loss = 0.0
    test_acc = 0.0
    total = 0.0

    for i, (inputs, labels) in enumerate(testloader):
        inputs, labels = inputs.cuda(), labels.cuda()
        inputs_var, labels_var = Variable(inputs), Variable(labels)
        
        outputs = model(inputs_var)
        loss = criterion(outputs, labels_var)

        _, pred = torch.max(outputs.data, 1)
        total += labels.size(0)
        test_loss += loss.data[0]
        test_acc += (pred == labels).sum()

    test_loss = test_loss / len(testloader)
    test_acc = test_acc / total
    return test_loss, test_acc 

def adjust_learning_rate(optimizer, learning_rate, epoch):
    if (epoch + 1) % 10 == 0:
        learning_rate = learning_rate / 10
    for param_group in optimizer.param_groups:
        param_group['lr'] = learning_rate
    return optimizer, learning_rate

def main():
    os.environ['CUDA_VISIBLE_DEVICES'] = args.gpu
    nclasses = 10
    epochs = args.epochs
    learning_rate = 0.1
    model_name = args.model_name

    trainloader, testloader = data_loader(model_name)
    model = cnn_model.CNNNet(model_name, nclasses=nclasses, pretrained=args.pretrained)
    model = model.cuda()
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.SGD(model.parameters(), lr=learning_rate)


    record = {}
    record['train loss'] = []
    record['train acc'] = []
    record['test loss'] = []
    record['test acc'] = []
    record['epoch time'] = []
    record['batch size'] = args.batch_size
    record['base lr'] = learning_rate
    record['pretrain'] = args.pretrained
    record['filename'] = 'log/' + model_name + '_' + datetime.now().strftime("%y-%m-%d-%H-%M-%S") + '.pkl'
    record['description'] = 'Model: base model\n'
    
    for epoch in range(epochs):
        epoch_time = time.time()
        train_loss, train_acc = train(trainloader, model, criterion, optimizer)
        train_time = time.time() - epoch_time
        print('[Epoch: %3d/%3d][Train Loss: %5.5f][Train Acc: %5.5f][Epoch Time: %3.3f]' % 
            (epoch, epochs, train_loss, train_acc, train_time))
        test_loss, test_acc = test(testloader, model, criterion)
        print('[Epoch: %3d/%3d][Test Loss: %5.5f][Test Acc: %5.5f]' % 
            (epoch, epochs, test_loss, test_acc))
        optimizer, learning_rate = adjust_learning_rate(optimizer, learning_rate, epoch)

        record['epoch time'].append(train_time)
        record['train loss'].append(train_loss)
        record['train acc'].append(train_acc)
        record['test loss'].append(test_loss)
        record['test acc'].append(test_acc)

    fp = open(record['filename'], 'wb')
    pickle.dump(record, fp)
    fp.close()


if __name__=="__main__":
    global args
    args = parser.parse_args()
    main()















