import transformers
from transformers import BertModel, BertTokenizer, AdamW, get_linear_schedule_with_warmup
import torch
import numpy as np
import pandas as pd
import argparse
from matplotlib import rc
from sklearn.model_selection import train_test_split
from sklearn.metrics import confusion_matrix, classification_report
from collections import defaultdict
from textwrap import wrap
from torch import nn, optim
from torch.utils.data import Dataset, DataLoader
import torch.nn.functional as F
import os
import subprocess
import logging
from pathlib import Path
from google.cloud import storage
import click
import matplotlib.pyplot as plt
import numpy as np
import torch
import io


from torch import nn, optim
# Local imports
from model import DepressionClassifier



BUCKET_NAME = "twitter-depression-classifier-bucket"
MODEL_FILE = "BERT_MODEL_dict.pt"

client = storage.Client()
bucket = client.get_bucket(BUCKET_NAME)
model_bin = bucket.get_blob(MODEL_FILE)
en_model = model_bin.download_as_string()
path = io.BytesIO(en_model)
class_names = ['Not Depressed', 'Depressed']
model = DepressionClassifier(len(class_names), 'bert-base-cased')
model.load_state_dict(torch.load(path, map_location=torch.device('cpu')))
tokenizer = BertTokenizer.from_pretrained('bert-base-cased')

def depression_classifier(request):
    """Predicts using trained model"""
    
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    
    request_json = request.get_json()
    if request_json and 'input_data' in request_json:
        data = request_json['input_data']
        
        encoded_review = tokenizer.encode_plus(data,
                                                max_length=160,
                                                add_special_tokens=True,
                                                return_token_type_ids=False,
                                                pad_to_max_length=True,
                                                return_attention_mask=True,
                                                return_tensors='pt')
        input_ids = encoded_review['input_ids'].to(device)
        attention_mask = encoded_review['attention_mask'].to(device)

        output = model(input_ids, attention_mask)
        _, prediction = torch.max(output, dim=1)
    
        return f'Sentiment  : {class_names[prediction]}'
    else:
        return "Prediction failed wrong json."