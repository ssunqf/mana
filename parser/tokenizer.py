#!/usr/bin/env python3.6
# -*- coding: utf-8 -*-
import torch
from pytorch_transformers import BertTokenizer, BertModel

tokenizer = BertTokenizer.from_pretrained(
    "bert-base-multilingual-cased", do_lower_case=False)

# model = BertModel.from_pretrained("bert-base-multilingual-cased")

text = "[CLS] Who was Jim Henson ? [SEP] Jim Henson was a puppeteer [SEP]"
tokenized_text = tokenizer.tokenize(text)
print(tokenized_text)

print(tokenizer.tokenize('[CLS]heyzo-0414 by arsenal-fan'))
print(tokenizer.tokenize('[CLS]KMHR-035R'))
print(tokenizer.tokenize('[CLS]第一會所新片@SIS001@(IDEAPOCKET)(IPZ-358)オレ専用家政婦_希志あいの'))