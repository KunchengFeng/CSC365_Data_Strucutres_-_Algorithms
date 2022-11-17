# CSC Assignment #2: Persistent Data Structures
import json
import tkinter as tk
from functools import partial


class BusinessesGUI(tk.Frame):

    def __init__(self, master, btree, clusters, tfidf, category, business_file):
        tk.Frame.__init__(self, master)

        # Main frame
        self.master = master
        self.frame = tk.Frame(self.master, bd=0, bg=Style.gray, width=1600, height=800)
        self.frame.pack()
        # Label
        self.title = tk.Label(self.frame, text="CSC365 Assignment 2", font=Style.font, fg=Style.green_d, bg=Style.gray)
        self.title.place(x=20, y=10)
        self.label = tk.Label(self.frame, text="Similar Businesses:", font=Style.font, fg=Style.green_d, bg=Style.gray)
        self.label.place(x=1175, y=55)
        # Search box
        self.entry = tk.Entry(self.frame, font=Style.font, fg=Style.white, bg=Style.gray, width=40, bd=4)
        self.entry.place(x=20, y=50)
        # Main text frame
        self.text_main = tk.Text(self.frame, font=Style.font, fg=Style.white, bg=Style.gray, width=108, height=29)
        self.set_text_main()
        # Side text frame
        self.text_side = tk.Text(self.frame, font=Style.font, fg=Style.green_d, bg=Style.gray, width=33, height=29)
        self.set_text_side()
        # Buttons for links
        self.button_cluster = []
        self.button_similar = []

        # ID search button
        action = partial(self.search_by_id, btree, clusters, tfidf, category, business_file)
        self.button_id = tk.Button(self.frame, text="Search by id", font=Style.font,
                                   fg=Style.green_d, bg=Style.gray, command=action)
        self.button_id.place(x=575, y=48)

        # Name search button
        action = partial(self.show_clusters, btree, clusters)
        self.button_name = tk.Button(self.frame, text="Show Clusters", font=Style.font,
                                     fg=Style.green_d, bg=Style.gray, command=action)
        self.button_name.place(x=750, y=48)

    def present_self(self, key, btree, clusters, tfidf, category_table, business_file):
        self.set_everything()
        line_key, line_file = key['line'], 0
        info = ""

        for entity in business_file:
            line_file += 1
            if line_file == line_key:
                business = json.loads(entity)
                name = business['name']
                address = business['address']
                city = business['city']
                state = business['state']
                postal = business['postal_code']
                category = category_table[key['id']]

                # Generate display information
                info = "\n" + name + "\n\n"
                info = info + "Address: " + address + ", " + city + ", " + state + ", " + postal + "\n"
                info = info + "Categories: {" + category + "}"
                business_file.seek(0)
                break

        self.text_main.insert(tk.END, info)
        # Find and display 10 most similar keys
        # Find the cluster this key belongs to, it's safe to assume the most similar key is in that cluster
        members = []
        most_sim = {}
        for i in range(len(clusters)):
            members = clusters[i]['Members']
            if key['id'] in members:
                # Compare current key with key center
                r_score = calculate_review_score(tfidf, key['id'], clusters[i]['Center'])
                c_score = calculate_category_score(category_table, key['id'], clusters[i]['Center'])
                similarity = r_score * 100 + c_score * 50
                most_sim[clusters[i]['Center']] = similarity
                break
            elif key['id'] == clusters[i]['Center']:
                break

        # Compare the current key with available members, save the ids of the 10 with highest score
        for i in range(len(members)):
            if key['id'] == members[i]:                                     # Don't want the key to compare to itself
                continue

            r_score = calculate_review_score(tfidf, key['id'], members[i])
            c_score = calculate_category_score(category_table, key['id'], members[i])
            similarity = r_score * 100 + c_score * 50                       # Review score tend to be very low

            if len(most_sim) >= 10:
                key_min = min(most_sim.keys(), key=(lambda k: most_sim[k]))
                if similarity >= most_sim[key_min]:
                    del most_sim[key_min]
                    most_sim[members[i]] = similarity
            else:
                most_sim[members[i]] = similarity
        most_sim = dict(sorted(most_sim.items(), key=lambda item: item[1], reverse=True))

        # Display 10 most similar businesses
        i = 0
        for each in most_sim:
            sim_key = search_key(btree, 'Root', each)
            name = sim_key['name']
            action = partial(self.present_self, sim_key, btree, clusters, tfidf, category_table, business_file)
            self.button_similar.append(tk.Button(self.text_side, text=name, font=Style.font,
                                                 fg=Style.green_l, bg=Style.gray, command=action))
            self.button_similar[i].pack()
            i += 1

        return None

    def set_text_main(self):
        self.text_main.delete("1.0", tk.END)
        self.text_main = tk.Text(self.frame, font=Style.font, fg=Style.white, bg=Style.gray, width=90, height=29)
        self.text_main.place(x=20, y=100)
        return None

    def set_text_side(self):
        self.text_side.delete("1.0", tk.END)
        self.text_side = tk.Text(self.frame, font=Style.font, fg=Style.green_d, bg=Style.gray, width=45, height=29)
        self.text_side.place(x=1025, y=100)
        return None

    def set_button_cluster(self):
        for i in range(len(self.button_cluster)):
            self.button_cluster[i].destroy()
        self.button_cluster = []
        return None

    def set_button_similar(self):
        for i in range(len(self.button_similar)):
            self.button_similar[i].destroy()
        self.button_similar = []
        return None

    def set_everything(self):
        self.set_text_main()
        self.set_text_side()
        self.set_button_cluster()
        self.set_button_similar()
        return None

    def search_by_id(self, btree, clusters, tfidf, category, business_file):
        self.set_everything()
        user_input = self.entry.get()
        key = search_key(btree, 'Root', user_input)
        if key is not None:
            self.present_self(key, btree, clusters, tfidf, category, business_file)
        else:
            self.text_main.insert(tk.END, "Did not find anything :(\n")
        return None

    def show_clusters(self, btree, clusters):
        self.set_everything()
        for i in range(len(clusters)):
            # Show the cluster center
            center_id = clusters[i]['Center']
            center_key = search_key(btree, 'Root', center_id)
            info = "\nCluster #" + str(i) + " Center: " + center_key['name'] + "(" + center_id + ")"

            # Make the text into a button
            action = partial(self.show_members, clusters, i)
            self.button_cluster.append(tk.Button(self.text_main, text=info, font=Style.font,
                                                 fg=Style.green_l, bg=Style.gray, command=action))
            self.button_cluster[i].pack()
        return None

    def show_members(self, clusters, nth):
        # Show all the members in nth cluster
        self.set_everything()
        info = ""
        for each in clusters[nth]['Members']:
            info = info + each + "\n"
        self.text_main.insert(tk.END, info)


class Style(object):
    gray = "#222629"
    white = "#FFFFFF"
    green_d = "#61892F"
    green_l = "#86C232"
    font = ("Verdana", 15)


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


def compare_id(b_id, key):
    key_id = key['id']
    if b_id == key_id:
        return 0
    elif b_id < key_id:
        return -1
    else:
        return 1


def load_file(file):
    with open(file, 'r') as j_file:
        print("Loading: " + str(file))
        data = json.load(j_file)
        j_file.close()
    return data


def search_key(tree, node, b_id):
    keys = tree[node]['Keys']
    children = tree[node]['Children']

    for i in range(len(keys)):
        result = compare_id(b_id, keys[i])
        if result == 0:
            return keys[i]
        elif result == -1:
            if len(children) != 0:
                return search_key(tree, children[i], b_id)
            else:
                return None
        elif result == 1:
            if len(children) != 0 and i == len(keys) - 1:
                return search_key(tree, children[i + 1], b_id)
            else:
                continue
    return None


def main():
    # Load up stuff
    btree = load_file("b-tree.json")
    clusters = load_file("clusters.json")
    tfidf = load_file("tf-idf.json")
    category = load_file("category.json")
    business_file = open("yelp_academic_dataset_business.json", 'r', encoding='utf-8')

    # Present the data
    root = tk.Tk()
    root.geometry("1600x800")
    BusinessesGUI(root, btree, clusters, tfidf, category, business_file)
    root.mainloop()
    business_file.close()


if __name__ == '__main__':
    main()
