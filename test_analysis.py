import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import json
import os
from tqdm import tqdm

steak_reviews = os.path.join("review_data", "johnny_prime_steaks.json")
with open(steak_reviews, "r", encoding="UTF-8-SIG") as f:
    review_data = json.load(f)

keywords = set([])

for review in tqdm(review_data):
    for spl in review["review"].split():
        try:
            keywords.add(spl)
        except:
            pass

word2vec = {}
word2int = {}

n = len(keywords)
for i, word in tqdm(enumerate(keywords)):
    oh = np.zeros(n, dtype=np.float32)
    oh[i] = 1
    word2vec[word] = oh
    word2int[word] = i

review_docs = np.zeros((len(review_data), len(word2vec)), dtype=np.float32)

for i, rev in tqdm(enumerate(review_data)):
    for spl in rev["review"].split():
        review_docs[i, word2int[spl]] += 1

tf_dict = review_docs[:]
tf = np.sum(tf_dict, axis=1, dtype=np.float32)
for i in tqdm(range(len(review_docs))):
    tf_dict[i] /= tf[i] + 0.01

N = len(review_docs)
idf_dict = np.zeros(len(word2vec), dtype=np.float32)
idoc = review_docs[:]
idoc[idoc > 1] = 1
df = np.sum(idoc, axis=0, dtype=np.float32)
for i in tqdm(range(len(word2vec))):    
    idf_dict[i] = np.log(N/(df[i]+0.01), dtype=np.float32)

tfidf = tf_dict[:]

for i in range(len(word2vec)):
    tfidf[:,i] /= idf_dict[i]

entity_ids = {
    "Beef": 270, "Beef Processed": 271, "Chicken": 272, "Ham": 274, "Lamb": 275, "Meat": 276, "Mutton": 277, "Pork": 278,
    "Buffalo": 521, "Mallard Duck": 551, "Other Meat Product": 787,}

molecule_word = set([])

commonWords = set([])

fdb_meat = {}

for k, v in tqdm(entity_ids.items()):
    dir = os.path.join("../", "FlavorDB_auto_download", "FlavorDB", f"{v}.json")
    with open(dir, "rb") as f:
        fdb_json = json.load(f)
        
    fdb_dict = {}
    for i in range(len(fdb_json["molecules"])):
        name, profile = fdb_json["molecules"][i]["common_name"], fdb_json["molecules"][i]["flavor_profile"]
        fdb_dict[name] = profile.split("@")
        
    fdb_meat.update(fdb_dict)
    
    for molecule in fdb_dict.keys():
        molecule_word.update(fdb_dict[molecule])
        
    yes = 0
    no = 0
    for word in molecule_word:
        if word not in keywords:
            no += 1
            print(word)
        else:
            yes += 1
            commonWords.add(word)
    print("Flavor Entity '{}' has been done".format(k))

mword2vec = {}
mword2int = {}

n = len(molecule_word)
for i, word in tqdm(enumerate(molecule_word)):
    oh = np.zeros(n, dtype=np.float32)
    oh[i] = 1
    mword2vec[word] = oh
    mword2int[word] = i

mdocs = np.zeros((len(molecule_word), len(mword2vec)), dtype=np.float32)
N = len(fdb_meat.keys())
for k in tqdm(fdb_meat.keys()):
    for word in fdb_meat[k]:
        mdocs[mword2int[word]] += 1

mtf_dict = mdocs[:]
mtf = np.sum(mtf_dict, axis=1, dtype=np.float32)
for i in range(len(mdocs)):
    mtf_dict[i] /= mtf[i] + 0.01

N = len(mdocs)
midf_dict = np.zeros(len(mword2vec), dtype=np.float32)
idoc = mdocs[:]
idoc[idoc > 1] = 1
df = np.sum(idoc, axis=0, dtype=np.float32)
for i in tqdm(range(len(mword2vec))):    
    midf_dict[i] = np.log(N/(df[i]+0.01), dtype=np.float32)

mtfidf = mtf_dict[:]

for i in range(len(mword2vec)):
    mtfidf[:,i] /= midf_dict[i]

rcommon = [word2int[w] for w in commonWords]
mcommon = [mword2int[w] for w in commonWords]

rctfidf = tfidf[:,rcommon]
mctfidf = mtfidf[:,mcommon]

mc = np.matmul(rctfidf, mctfidf.T, dtype=np.float32)

print(mc.shape)

for i in range(N):
    ss = sorted(range(len(mc[i])), key=lambda k: mc[i][k], reverse=True)
    if np.max(mc[i]) > 0:
        break

print(review_data[i]["place"])

with open("test_result.txt", "w") as f:
    for s in ss:
        f.write("{} : {:.2e}\n".format(list(fdb_meat.keys())[s], mc[i][s]))

plt.title("reviews over molecules")
plt.imshow(mc)
plt.savefig("test_result.png", dpi=300, format="png")