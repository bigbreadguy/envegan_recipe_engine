import os
import requests
import json

def get_entity(index:int):
    url = f"https://cosylab.iiitd.edu.in/flavordb/entities_json?id={index}"
    data = requests.get(url).json()

    return data

def save_into_json(data, db_dir):
    file_name = os.path.join(db_dir, "%d.json" % index)
    with open(file_name,'w') as f:
        json.dump(data, f, indent=4, sort_keys=True)

if __name__ == "__main__":
    cwd_dir = os.getcwd()
    db_dir = os.path.join(cwd_dir, "FlavorDB")

    if not os.path.exists(db_dir):
        os.makedirs(db_dir)

    for index in range(1000):
        try:
            data = get_entity(index)

            name_key = "entity_alias_readable"
            name = data[name_key]

            print("Downloading %s data" % name)
            
            save_into_json(data, db_dir)

            index+=1
        except:
            continue

    print("Done")
