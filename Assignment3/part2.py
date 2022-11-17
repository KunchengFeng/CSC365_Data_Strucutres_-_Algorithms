# Select a node then display it's shortest path
import json
import tkinter as tk
from functools import partial


class BusinessesGUI(tk.Frame):

    def __init__(self, master, tree, tf_idf, cate, close, b_file):
        tk.Frame.__init__(self, master)

        # Main frame
        self.master = master
        self.frame = tk.Frame(self.master, bd=0, bg=Style.gray, width=1600, height=800)
        self.frame.pack()
        # Label
        self.title = tk.Label(self.frame, text="CSC365 Assignment 3", font=Style.font, fg=Style.green_d, bg=Style.gray)
        self.title.place(x=20, y=10)
        self.label = tk.Label(self.frame, text="Shortest Path:", font=Style.font, fg=Style.green_d, bg=Style.gray)
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
        self.button_similar = tk.Button(self.text_side, text="", font=Style.font,
                                        fg=Style.green_l, bg=Style.gray)

        # ID search button
        action = partial(self.search_by_id, tree, close, tf_idf, cate, b_file)
        self.button_id = tk.Button(self.frame, text="Search by id", font=Style.font,
                                   fg=Style.green_d, bg=Style.gray, command=action)
        self.button_id.place(x=575, y=48)

    def present_self(self, key, tree, close, tf_idf, category_table, b_file):
        self.set_everything()
        line_key, line_file = key['line'], 0
        info = ""

        for entity in b_file:
            line_file += 1
            if line_file == line_key:
                business = json.loads(entity)
                b_id = business['business_id']
                name = business['name']
                address = business['address']
                city = business['city']
                state = business['state']
                postal = business['postal_code']
                cate = category_table[key['id']]

                # Generate display information
                info = "\n" + name + "\n\n"
                info = info + "Business id: " + b_id + "\n"
                info = info + "Address: " + address + ", " + city + ", " + state + ", " + postal + "\n"
                info = info + "Categories: {" + cate + "}"
                b_file.seek(0)
                break

        self.text_main.insert(tk.END, info)

        # Find the most similar link
        sim_scores = {}
        for link in close[key['id']]:
            r_score = calculate_review_score(tf_idf, key['id'], link)
            c_score = calculate_category_score(category_table, key['id'], link)
            similarity = r_score * 100 + c_score * 50
            sim_scores[link] = similarity
        most_sim = max(sim_scores.keys(), key=(lambda k: sim_scores[k]))

        # Display closest path
        sim_key = search_key(tree, 'Root', most_sim)
        name = sim_key['name']
        action = partial(self.present_self, sim_key, tree, close, tf_idf, category_table, b_file)
        self.button_similar = tk.Button(self.text_side, text=name, font=Style.font,
                                        fg=Style.green_l, bg=Style.gray, command=action)
        self.button_similar.pack()

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

    def set_button_similar(self):
        self.button_similar.destroy()
        return None

    def set_everything(self):
        self.set_text_main()
        self.set_text_side()
        self.set_button_similar()
        return None

    def search_by_id(self, tree, close, tf_idf, cate, b_file):
        self.set_everything()
        user_input = self.entry.get()
        key = search_key(tree, 'Root', user_input)
        if key is not None:
            self.present_self(key, tree, close, tf_idf, cate, b_file)
        else:
            self.text_main.insert(tk.END, "Did not find anything :(\n")
        return None


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


def calculate_review_score(tf_idf, id_this, id_other):
    review_score = 0
    try:  # Some business might not have reviews
        for term in tf_idf[id_this]:
            try:  # Check if 2 business share the same term in review
                weight1 = tf_idf[id_this][term]
                weight2 = tf_idf[id_other][term]
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


def load_file(file_name):
    print("Loading " + file_name + " file...")
    with open(file_name, 'r') as file:
        data = json.load(file)
        file.close()
    print("Loaded " + file_name + " file.")
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


if __name__ == '__main__':
    # Load up stuff
    btree = load_file("b-tree.json")
    tfidf = load_file("tf-idf.json")
    category = load_file("category.json")
    closest = load_file("closest_businesses.json")
    business_file = open("yelp_academic_dataset_business.json", 'r', encoding='utf-8')

    # Present the data
    root = tk.Tk()
    root.geometry("1600x800")
    BusinessesGUI(root, btree, tfidf, category, closest, business_file)
    root.mainloop()
    business_file.close()
