#!/usr/bin/env python3.6
# -*- coding: utf-8 -*-
import asyncio
import sys
import re
from sentencepiece import SentencePieceTrainer as Trainer, SentencePieceProcessor as Tokenizer
from util import database
from tqdm import tqdm

serial = r'"[a-f0-9]{20,}"'
async def write(queue, output):
    tq = tqdm(desc='write')
    with open(output, 'wt') as out:
        while True:
            item = await queue.get()
            if item is None:
                break
            if not re.fullmatch(serial, item):
                text = text[1:-1]
                text = re.sub('â€“', '-', text)
                text = re.sub('â”€', '─', text)
                text = re.sub('â€¢', '•', text)
                text = re.sub('â˜†', '☆', text)
                text = re.sub('â€™', '’', text)
                text = re.sub('â€Ž', '', text)
                text = re.sub('Ñ€', 'p', text)
                out.write(item[1:-1]+'\n')
            tq.update()


def fetch_text(text_file, loop=None):
    if loop is None:
        loop = asyncio.get_event_loop()
    torrent = database.Torrent('207.148.124.42', loop=loop)
    queue = asyncio.Queue(10000)
    loop.run_until_complete(asyncio.gather(torrent.fetch_text(queue), write(queue, text_file)))


if __name__ == '__main__':
    # fetch_text(sys.argv[1])
    Trainer.Train(f'--input={sys.argv[1]} --model_prefix={sys.argv[2]} --vocab_size={sys.argv[3]}')

    tokenizer = Tokenizer()
    tokenizer.Load('spm.model')
    with open(sys.argv[1]) as input:
        for line in input:
            print(line)
            print(tokenizer.encode_as_pieces(line))