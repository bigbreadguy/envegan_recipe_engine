import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import json
import os
from tqdm import tqdm

analysis_result = os.path.join(os.getcwd(), "analysis_result")
if not os.path.exists(analysis_result):
    os.makedirs(analysis_result)

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

mword2int = {}

n = len(molecule_word)
for i, word in tqdm(enumerate(molecule_word)):
    mword2int[word] = i

mole2vec = {}

n = len(molecule_word)
for mole in tqdm(fdb_meat.keys()):
    oh = np.zeros(n, dtype=np.float32)
    for j, word in enumerate(molecule_word):
        if word in fdb_meat[mole]:
            oh[j] = 1
    mole2vec[mole] = oh

mdocs = np.zeros((len(mole2vec), len(molecule_word)), dtype=np.float32)
N = len(fdb_meat.keys())
for i, k in tqdm(enumerate(fdb_meat.keys())):
    for word in fdb_meat[k]:
        mdocs[i, mword2int[word]] += 1

mtf_dict = mdocs.copy()
mtf = np.sum(mtf_dict, axis=1, dtype=np.float32)
for i in range(len(mdocs)):
    mtf_dict[i, :] /= mtf[i] + 0.01

N = len(mdocs)
midf_dict = np.zeros(len(molecule_word), dtype=np.float32)
idoc = mdocs.copy()
idoc[idoc > 1] = 1
df = np.sum(idoc, axis=0, dtype=np.float32)
for i in tqdm(range(len(molecule_word))):    
    midf_dict[i] = np.log(N/(df[i]+0.01), dtype=np.float32)

mtfidf = mtf_dict[:]

for i in range(len(molecule_word)):
    mtfidf[:,i] /= midf_dict[i]

print(f"common words: {commonWords}")
print(f"count: {len(commonWords)}")

rcommon = [word2int[w] for w in commonWords]
mcommon = [mword2int[w] for w in commonWords]

rctfidf = tfidf[:,rcommon]
mctfidf = mtfidf[:,mcommon] #mctfidf가 잘못 구해짐

plt.title("reviews over words")
plt.imshow(rctfidf)
plt.savefig(os.path.join(analysis_result, "rctfidf.png"), dpi=300, format="png")

plt.title("molecules over words")
plt.imshow(mctfidf)
plt.savefig(os.path.join(analysis_result, "mctfidf.png"), dpi=300, format="png")

mc = np.matmul(rctfidf, mctfidf.T, dtype=np.float32)

print(mc.shape)

rm_result = os.path.join(analysis_result, "review-molecule")
if not os.path.exists(rm_result):
    os.makedirs(rm_result)

for i in range(len(mole2vec)):
    ss = sorted(range(len(mc[i])), key=lambda k: mc[i][k], reverse=True)
    
    with open(os.path.join(rm_result, f"{review_data[i]['place']}.txt"), "w") as f:
        f.write("molecule, intensity\n")
        for s in ss:
            f.write("{}, {:.2e}\n".format(list(fdb_meat.keys())[s], mc[i][s]))

plt.title("reviews over molecules")
plt.imshow(mc)
plt.savefig(os.path.join(analysis_result, "test_result.png"), dpi=300, format="png")

flavor_db = os.path.join(os.getcwd(), "flavor_db")
entities = os.listdir(flavor_db)

categories = set([])

data_dicts = []

for entity in entities:
    with open(os.path.join(flavor_db, entity)) as f:
        data_dict = json.load(f)
        data_dicts.append(data_dict)
        
    categories.add(data_dict["category_readable"])

vegan_categories = ('Spice', 'Plant Derivative', 'Cereal', 'Seed', 'Legume',
                    'Vegetable', 'Fruit', 'Vegetable Root', 'Maize', 'Vegetable Fruit',
                    'Berry', 'Vegetable Stem', 'Nut', 'Fruit-Berry','Vegetable Tuber',
                    'Herb', 'Fungus', 'Essential Oil', 'Fruit Essence', 'Cabbage',
                    'Fruit Citrus', 'Plant', 'Flower')

vegan_entities = []

for entity in data_dicts:
    if entity["category_readable"] in vegan_categories:
        print(entity["entity_alias_readable"])
        vegan_entities.append(entity)

fdb_veg = {}
veg_profiles = set([])

for entity in vegan_entities:
    name = entity["entity_alias_readable"]
    
    profiles = []
    for molecule in entity["molecules"]:
        profiles.extend(molecule["flavor_profile"].split("@"))
    
    fdb_veg[name] = profiles
    veg_profiles.update(profiles)

prof2int = {}
for i, prof in enumerate(veg_profiles):
    prof2int[prof] = i

vdoc = np.zeros((len(fdb_veg), len(veg_profiles)), dtype=np.float32)
veg2int = {}

for i, name, profiles in enumerate(fdb_veg.items()):
    veg2int[name] = i

    for prof in profiles:
        j = prof2int[prof]
    
    vdoc[i, j] += 1

vtfidf = vdoc[:]
for i in range(len(fdb_veg)):
    vtf = np.sum(vtfidf[i, :], dtype=np.float32)
    vtfidf[i, :] /= vtf

vcommon = [prof2int[w] for w in commonWords]

vctfidf = vtfidf[:, vcommon]

rv = np.matmul(rctfidf, vctfidf.T, dtype=np.float32)

rv_result = os.path.join(analysis_result, "review-vegan")
if not os.path.exists(rv_result):
    os.makedirs(rv_result)

for i in range(N):
    ss1 = sorted(range(len(rv[i])), key=lambda k: rv[i][k], reverse=True)
    
    with open(os.path.join(rv_result, f"{review_data[i]['place']}.txt"), "w") as f:
        f.write("vegan_entity, intensity\n")
        for s in ss:
            f.write("{}, {:.2e}\n".format(list(fdb_veg.keys())[s], rv[i][s]))