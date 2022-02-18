import os
import json
from scipy.spatial.distance import cosine
from transformers import BertTokenizer, BertModel
import pandas as pd
import numpy as np
import nltk
import torch

def bert_text_preparation(text, tokenizer):
    """Preparing the input for BERT
    
    Takes a string argument and performs
    pre-processing like adding special tokens,
    tokenization, tokens to ids, and tokens to
    segment ids. All tokens are mapped to seg-
    ment id = 1.
    
    Args:
        text (str): Text to be converted
        tokenizer (obj): Tokenizer object
            to convert text into BERT-re-
            adable tokens and ids
        
    Returns:
        list: List of BERT-readable tokens
        obj: Torch tensor with token ids
        obj: Torch tensor segment ids
    
    
    """
    marked_text = "[CLS] " + text + " [SEP]"
    tokenized_text = tokenizer.tokenize(marked_text)
    indexed_tokens = tokenizer.convert_tokens_to_ids(tokenized_text)
    segments_ids = [1]*len(indexed_tokens)

    # Convert inputs to PyTorch tensors
    tokens_tensor = torch.tensor([indexed_tokens])
    segments_tensors = torch.tensor([segments_ids])

    return tokenized_text, tokens_tensor, segments_tensors

def get_bert_embeddings(tokens_tensor, segments_tensors, model):
    """Get embeddings from an embedding model
    
    Args:
        tokens_tensor (obj): Torch tensor size [n_tokens]
            with token ids for each token in text
        segments_tensors (obj): Torch tensor size [n_tokens]
            with segment ids for each token in text
        model (obj): Embedding model to generate embeddings
            from token and segment ids
    
    Returns:
        list: List of list of floats of size
            [n_tokens, n_embedding_dimensions]
            containing embeddings for each token
    
    """
    
    # Gradient calculation id disabled
    # Model is in inference mode
    with torch.no_grad():
        outputs = model(tokens_tensor, segments_tensors)
        # Removing the first hidden state
        # The first state is the input state
        hidden_states = outputs[2][1:]

    # Getting embeddings from the final BERT layer
    token_embeddings = hidden_states[-1]
    # Collapsing the tensor into 1-dimension
    token_embeddings = torch.squeeze(token_embeddings, dim=0)
    # Converting torchtensors to lists
    list_token_embeddings = [token_embed.tolist() for token_embed in token_embeddings]

    return list_token_embeddings

if __name__ == "__main__":
    model = BertModel.from_pretrained('bert-base-uncased',
                                  output_hidden_states = True,
                                  )

    tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')

    steak_reviews = os.path.join("review_data", "johnny_prime_steaks.json")
    with open(steak_reviews, "r", encoding="UTF-8-SIG") as f:
        review_data = json.load(f)

    texts = [data["review"] for data in review_data]

    target_word_embeddings = []

    for text in texts:
        tokenized_text, tokens_tensor, segments_tensors = bert_text_preparation(text, tokenizer)
        list_token_embeddings = get_bert_embeddings(tokens_tensor, segments_tensors, model)
        
        word_index = tokenized_text.index('meat')
        word_embedding = list_token_embeddings[word_index]

        target_word_embeddings.append(word_embedding)

    list_of_distances = []
    for text1, embed1 in zip(texts, target_word_embeddings):
        for text2, embed2 in zip(texts, target_word_embeddings):
            cos_dist = 1 - cosine(embed1, embed2)
            list_of_distances.append([text1, text2, cos_dist])

    distances_df = pd.DataFrame(list_of_distances, columns=['text1', 'text2', 'distance'])

    distances_df[distances_df.text1 == 'meat']

    distances_df[distances_df.text1 == 'fatty flavor, juicy meat']

    cos_dist = 1 - cosine(target_word_embeddings[0], np.sum(target_word_embeddings, axis=0))
    print(f'Distance between context-free and context-averaged = {cos_dist}')
