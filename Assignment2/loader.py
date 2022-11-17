# CSC 365 Assignment #2: Persistent Data Structures
import json
import math
import random
import string
from nltk.corpus import stopwords


# Calculate k clusters
def calculate_cluster(tree, k):
    # Initialize stuff
    with open("tf-idf.json", 'r') as file:
        print("Loading TFIDF file")
        tfidf = json.load(file)
        file.close()
        print("TF-IDF loaded for cluster calculation")
    with open("category.json", 'r') as file:
        print("Loading category file")
        category = json.load(file)
        file.close()
        print("Category loaded for cluster calculation")
    keys = []                                               # Append all keys to an array for easier organization
    for node in tree:
        for key in tree[node]['Keys']:
            keys.append(key)
    clusters = []                                           # Base case
    for i in range(k):
        clusters.append({'Cluster_Score': 0})

    # Associate all keys to their most similar cluster, try this 10 times, override the each turns out better
    for i in range(10):
        picked_ids = pick_keys(keys, k)
        new_clusters = []
        for j in range(k):
            new_clusters.append({'Center': picked_ids[j], 'Members': [], 'Cluster_Score': 0})

        for key in keys:                                                    # Compare each key to cluster centers
            if key['id'] not in picked_ids:
                scores = {}                                                 # Tiny hashtable for score keeping
                for key_center in picked_ids:
                    r_score = calculate_review_score(tfidf, key['id'], key_center)
                    c_score = calculate_category_score(category, key['id'], key_center)
                    similarity = r_score * 100 + c_score * 50               # Review score tend to be very low
                    scores[key_center] = similarity                         # Assign a sim score to cluster center

                key_best = max(scores.keys(), key=(lambda x: scores[x]))        # Found the best cluster to insert to
                for j in range(len(new_clusters)):
                    if new_clusters[j]['Center'] == key_best:
                        new_clusters[j]['Members'].append(key['id'])
                        new_clusters[j]['Cluster_Score'] += scores[key_best]

        # Compare to see if new cluster is better than the old one
        score_old, score_new = 0, 0
        print("Attempt number " + str(i) + ", Picked keys:")
        for j in range(k):                                    # K amount of clusters
            score_old += clusters[j]['Cluster_Score']
            score_new += new_clusters[j]['Cluster_Score']
            print(picked_ids[j])
        print("Total similarity score: " + str(score_new))

        if score_new > score_old:                                      # Overwrite the old cluster if found a better one
            clusters = new_clusters

    with open("clusters.json", "w") as file:
        json.dump(clusters, file, indent=4)
        file.close()
        print("Cluster calculation completed")
    return None


# Calculate the category similarity by finding the jaccard similarity of categories
def calculate_category_score(category_table, id_x, id_y):
    category_x = category_table[id_x]
    category_y = category_table[id_y]

    if category_x is not None:
        category_x = set(category_x.replace(' ', '').split(","))
    else:
        category_x = set()

    if category_y is not None:
        category_y = set(category_y.replace(' ', '').split(","))
    else:
        category_y = set()

    try:
        common = len(category_x.intersection(category_y))
        total = len(category_x.union(category_y))
        category_score = round(common/total, 4)
    except ZeroDivisionError:
        category_score = 0
    return category_score


# Calculate the review similarity by add up tfidf value of shared terms and /2
def calculate_review_score(tfidf, id_this, id_other):
    review_score = 0
    try:  # Some business might not have reviews
        for term in tfidf[id_this]:
            try:  # Check if 2 business share the same term in review
                weight1 = tfidf[id_this][term]
                weight2 = tfidf[id_other][term]
                review_score += round((weight1+weight2)/2, 4)
            except KeyError:
                continue
    except KeyError:
        pass
    return review_score


# Calculate the weight of each term in each business reviews
def calculate_tfidf(tfidf_file, tf_file, df_file):
    # Load the term frequency file
    with open(tf_file, 'r') as file:
        print("Loading term frequency file")
        tf = json.load(file)
        file.close()
        print("Loaded term frequency file")

    # Load the document frequency file
    with open(df_file, 'r') as file:
        print("Loading document frequency file")
        df = json.load(file)
        file.close()
        print("Loaded document frequency file")

    # Calculate the TF-IDF of each term in each business
    tfidf = {}
    total_docs = len(tf)
    print("Calculating TFIDF")
    for doc in tf:
        tfidf[doc] = {}
        doc_words = 0
        for term in tf[doc]:
            doc_words += tf[doc][term]
        for term in tf[doc]:
            weight = (tf[doc][term] / doc_words) * math.log(total_docs / df[term])
            if weight < 0.01:       # I'm not keeping something that counts less than 1 percent
                continue
            else:
                tfidf[doc][term] = round(weight, 4)

    # Write TF-IDF in to persistent file
    with open(tfidf_file, 'w') as file:
        json.dump(tfidf, file, indent=4)
        print("TFIDF calculated")
        file.close()
    return None


def compare(key_this, key_other):
    # Compare the inserted id to the one saved in the key
    id_this = key_this['id']
    id_other = key_other['id']
    if id_this == id_other:
        return 0
    elif id_this < id_other:
        return -1
    else:
        return 1


def compare_id(b_id, key):
    key_id = key['id']
    if b_id == key_id:
        return 0
    elif b_id < key_id:
        return -1
    else:
        return 1


# Try to insert key into the right node, then promote if keys are full
def insert(tree, node, key):
    keys = tree[node]['Keys']
    kids = tree[node]['Children']

    if len(keys) != 0:
        for i in range(len(keys)):
            result = compare(key, keys[i])
            if result == 0:                                         # Key already exist in tree
                return tree
            elif result == -1:
                if len(kids) != 0:                                  # Insert key at children[i]
                    return insert(tree, kids[i], key)
                else:
                    tree[node]['Keys'].append(key)
                    tree[node]['Keys'].sort(key=lambda x: x['id'])
                    if len(keys) == 65:                             # Now node_this have 65 keys, time to promote
                        return promote(tree, node)
                    else:
                        return tree
            else:
                if i == len(keys) - 1:                              # Reached the end of keys
                    if len(kids) == 0:
                        tree[node]['Keys'].append(key)
                        tree[node]['Keys'].sort(key=lambda x: x['id'])
                        if len(keys) == 65:                         # Now node_this have 65 keys, time to promote
                            return promote(tree, node)
                        else:
                            return tree
                    else:                                           # Insert key at children[i+1]
                        return insert(tree, kids[i+1], key)
                else:
                    continue
    else:
        tree[node]['Keys'].append(key)                              # First key
        return tree


def inherit_keys(tree, keys, node, index):
    for i in range(32):
        tree[node]['Keys'].append(keys[i + index])
    return tree


def inherit_kids(tree, kids, node, index):
    for i in range(33):
        tree[node]['Children'].append(kids[i + index])
        tree[kids[i + index]]['Parent'] = node
    return tree


def new_key(business, i):
    # Create a dictionary, load it with business information, then return it.
    key = {'id': business['business_id'], 'name': business['name'], 'line': i}
    return key


# Try to find a name for the new node
def new_node_name(tree):
    found = False
    name = "Subtree_" + str(random.randint(0, 9999))
    while not found:
        if name in tree:
            name = "Subtree_" + str(random.randint(0, 9999))
        else:
            found = True
    return name


# Promote middle key to parent node, then call split function
def promote(tree, node_this):
    tree[node_this]['Keys'].sort(key=lambda x: x['id'])
    keys = tree[node_this]['Keys']
    parent = tree[node_this]['Parent']

    if len(keys) == 65:                                     # This node is full, promote and split
        if node_this == 'Root':                             # Root node is full, split into two
            return split_root(tree)
        else:
            tree[parent]['Keys'].append(keys[32])
            tree[parent]['Keys'].sort(key=lambda x: x['id'])

            tree = split_child(tree, parent, node_this)
            return promote(tree, parent)                    # Parent node might need a promotion too
    else:
        return tree


# Return the an k length array containing the ids of k picked keys
def pick_keys(keys, k):
    picks = []
    for num in range(k):
        key_id = keys[random.randint(0, len(keys) - 1)]['id']
        if key_id not in picks:
            picks.append(key_id)
        else:
            num -= 1
    return picks


# Return the line value in key (if found)
def search(tree, node, b_id):
    keys = tree[node]['Keys']
    children = tree[node]['Children']

    for i in range(len(keys)):
        result = compare_id(b_id, keys[i])
        if result == 0:
            return keys[i]['line']
        elif result == -1:
            if len(children) != 0:
                return search(tree, children[i], b_id)
            else:
                return 0
        elif result == 1:
            if len(children) != 0 and i == len(keys) - 1:
                return search(tree, children[i + 1], b_id)
            else:
                continue
    return 0


def split_child(tree, parent, node_this):
    keys = tree[node_this]['Keys']
    kids = tree[node_this]['Children']

    # Reassign keys and kids
    node_new = new_node_name(tree)
    tree[node_this] = {'Keys': [], 'Children': [], 'Parent': parent}
    tree[node_new] = {'Keys': [], 'Children': [], 'Parent': parent}
    tree = inherit_keys(tree, keys, node_this, 0)
    tree = inherit_keys(tree, keys, node_new, 33)
    if len(kids) != 0:
        tree = inherit_kids(tree, kids, node_this, 0)
        tree = inherit_kids(tree, kids, node_new, 33)

    # Need to know which kid aim I splitting
    nth_kid = 0
    siblings = tree[parent]['Children']
    for i in range(len(siblings)):
        if siblings[i] == node_this:
            nth_kid = i
            break

    # Make a room for the nth child
    tree[parent]['Children'].append('Temp')
    for i in reversed(range(len(tree[parent]['Children']))):
        if i == nth_kid:
            break
        else:
            tree[parent]['Children'][i] = tree[parent]['Children'][i - 1]
    tree[parent]['Children'][nth_kid + 1] = node_new

    return tree


def split_root(tree):
    # Temporarily save them
    keys = tree['Root']['Keys']
    kids = tree['Root']['Children']
    # Reset the root node
    tree['Root'] = {'Keys': [], 'Children': [], 'Parent': 'Root'}
    tree['Root']['Keys'].append(keys[32])

    # Make 2 new nodes
    node_left = new_node_name(tree)
    node_right = new_node_name(tree)
    tree[node_left] = {'Keys': [], 'Children': [], 'Parent': 'Root'}
    tree[node_right] = {'Keys': [], 'Children': [], 'Parent': 'Root'}

    # Inherit kids if root have any
    if len(kids) != 0:
        tree = inherit_kids(tree, kids, node_left, 0)
        tree = inherit_kids(tree, kids, node_right, 33)

    # Inherit keys
    tree = inherit_keys(tree, keys, node_left, 0)               # Left node inherit key #0 ~ 31
    tree = inherit_keys(tree, keys, node_right, 33)             # Right node inherit key #33 ~ 65
    tree['Root']['Children'].append(node_left)
    tree['Root']['Children'].append(node_right)

    return tree


def load_b_tree(file):
    try:
        # Load up saved B Tree file
        with open(file, 'r') as j_file:
            tree = json.load(j_file)
            j_file.close()
    except FileNotFoundError:
        # Initialize the B Tree if none found
        tree = {'Root': {'Keys': [], 'Children': [], 'Parent': 'Root'}}
    except json.decoder.JSONDecodeError:
        # Write a new tree anyway.
        tree = {'Root': {'Keys': [], 'Children': [], 'Parent': 'Root'}}
    print("B-Tree loaded")
    return tree


def load_reviews(tree, yelp, tf, df):
    table_tf = {}
    table_df = {}
    counter = 0
    unwanted = stopwords.words('english')

    for line in open(yelp, 'r', encoding='utf-8'):
        review = json.loads(line)
        b_id = review["business_id"]

        # Check if the business is in the B-Tree
        if search(tree, 'Root', b_id) != 0:
            counter += 1

            # Filter the words
            review_text = review["text"]
            review_text = review_text.translate(str.maketrans('', '', string.punctuation))
            bag_of_words = review_text.replace('\n', ' ').split(' ')
            words_filtered = []
            for word in bag_of_words:
                if word.lower() in unwanted:
                    pass
                elif word == '':
                    pass
                else:
                    words_filtered.append(word)

            # Associate words with business id in term frequency
            # Each business count as a document for easier organization
            try:
                terms = table_tf[b_id]
            except KeyError:
                terms = {}

            for word in words_filtered:
                try:
                    terms[word.lower()] += 1
                except KeyError:
                    terms[word.lower()] = 1
                    try:
                        table_df[word.lower()] += 1
                    except KeyError:
                        table_df[word.lower()] = 1
            table_tf[b_id] = terms

            if counter == 5000:
                print("5000 Reviews Added")
                counter = 0

    # Write to term frequency file
    with open(tf, 'w') as tf_file:
        json.dump(table_tf, tf_file, indent=4)
        print("Term frequency updated")
        tf_file.close()

    # Write to document frequency file
    with open(df, 'w') as df_file:
        json.dump(table_df, df_file, indent=4)
        print("Document frequency updated")
        df_file.close()

    return None


def update_b_tree(tree, yelp, c_file, t_file):
    # Modify the B Tree file with each loop through the business file.
    counter, line = 0, 0
    category_table = {}
    with open(yelp, 'r', encoding='utf-8') as business_file, \
            open(t_file, 'w') as tree_file:
        for each in business_file:
            line += 1  # Line starts at 1
            entity = json.loads(each)
            if entity['is_open'] == 1:
                category = entity['categories']
                b_id = entity['business_id']
                category_table[b_id] = category

                key = new_key(entity, line)
                tree = insert(tree, 'Root', key)

                counter += 1
                if counter == 2500:     # Rewrite per 2500 new keys
                    tree_file.seek(0)   # Rewind
                    json.dump(tree, tree_file, indent=4)
                    print("Inserted 2500 keys")
                    counter = 0

        # Rewrite file one more time just before closes
        tree_file.seek(0)  # Rewind
        json.dump(tree, tree_file, indent=4)
        print("Tree updated")
        business_file.close()
        tree_file.close()

    with open(c_file, 'w') as category_file:
        json.dump(category_table, category_file, indent=4)
        print("Category saved")
        category_file.close()

    return tree


def main():
    tree = load_b_tree("b-tree.json")
    tree = update_b_tree(tree, "yelp_academic_dataset_business.json", "category.json", "b-tree.json")
    load_reviews(tree, "yelp_academic_dataset_review.json", "term-frequency.json", "document-frequency.json")
    calculate_tfidf("tf-idf.json", "term-frequency.json", "document-frequency.json")
    calculate_cluster(tree, 10)
    print("Loader.py finished")


if __name__ == '__main__':
    main()
