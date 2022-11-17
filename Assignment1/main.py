# CSC 365 Assignment #1: Yelp dataset recommendation system.
import json
import string
import tkinter as tk
from functools import partial
from nltk.corpus import stopwords


# Business class
class Business(object):
    name = ""
    address = ""
    city = ""
    state = ""
    postal_code = ""
    categories = {}
    word_table = {}
    similarity = 0


def new_business(b_info):
    b_obj = Business()
    b_obj.name = b_info["name"]
    b_obj.address = b_info["address"]
    b_obj.city = b_info["city"]
    b_obj.state = b_info["state"]
    b_obj.postal_code = b_info["postal_code"]
    b_obj.categories = b_info["categories"]
    b_obj.word_table = {}
    return b_obj


# Put the still open businesses into a hash table with id as key.
def load_business(table):
    amount = 0
    for each in open('yelp_academic_dataset_business.json', encoding='utf-8'):
        entity = json.loads(each)
        if entity['is_open'] == 1:
            business = new_business(entity)
            table[entity["business_id"]] = business
            amount += 1
            if amount >= 10000:
                break
    return table


# Associate the reviews with the business
def load_reviews(table):
    count = 0
    unwanted = stopwords.words('english')
    for line in open('yelp_academic_dataset_review.json', encoding='utf-8'):
        review = json.loads(line)
        b_id = review["business_id"]
        # Check if the business is in the list
        try:
            this_buss = table[b_id]
        except KeyError:
            continue

        # Filter the words
        review_text = review["text"]
        review_text = review_text.translate(str.maketrans('', '', string.punctuation))
        bag_of_words = review_text.replace('\n', ' ').split(' ')
        wanted_words = []
        for word in bag_of_words:
            if word.lower() in unwanted:
                pass
            elif word == '':
                pass
            else:
                wanted_words.append(word)

        # Associate the words with businesses
        for word in wanted_words:
            try:
                this_buss.word_table[word] += 1
            except KeyError:
                this_buss.word_table[word] = 1

        # Limiting data size
        count += 1
        if count >= 50000:
            break
    return table


# Save only 10 most used words
def sort_word(b_info):
    original_set = b_info.word_table
    new_set = {}
    for word_key in original_set:
        if word_key == '':
            pass
        elif len(new_set) >= 10:
            key_min = min(new_set.keys(), key=(lambda k: new_set[k]))
            if original_set[word_key] >= new_set[key_min]:
                del new_set[key_min]
                new_set[word_key] = original_set[word_key]
        else:
            new_set[word_key] = original_set[word_key]
    return new_set


# Compare 2 businesses and return similarity score
def sim_score(buss_this, buss_other):
    score = 0
    cate_this = []
    cate_other = []

    # Add scores from categories
    if buss_this.categories is not None:
        cate_this = buss_this.categories.split(",")
    if buss_other.categories is not None:
        cate_other = buss_other.categories.split(",")

    for i in range(len(cate_this)):
        for j in range(len(cate_other)):
            if cate_this[i] == cate_other:
                score += 10

    # Add scores from frequent words
    word_this = buss_this.word_table
    word_other = buss_other.word_table
    for word in word_this:
        try:
            if word_other[word] is not None:
                score += 2
        except KeyError:
            pass
    return score


# GUI Variables
class Style(object):
    gray = "#222629"
    white = "#FFFFFF"
    green_d = "#61892F"
    green_l = "#86C232"
    head = ("Helvetica", 15)
    body = ("Verdana", 15)


# Create GUI
class BusinessesGUI(tk.Frame):

    def __init__(self, master, table):
        tk.Frame.__init__(self, master)

        # Main frame
        self.master = master
        self.frame = tk.Frame(self.master, bd=0, bg="#222629", width=1600, height=800)
        self.frame.pack()
        # Label
        self.title = tk.Label(self.frame, text="CSC365 Assignment 1", font=Style.head, fg=Style.green_d, bg=Style.gray)
        self.title.place(x=20, y=10)
        self.label = tk.Label(self.frame, text="Similar Businesses:", font=Style.head, fg=Style.green_d, bg=Style.gray)
        self.label.place(x=1175, y=55)
        # Search box
        self.entry = tk.Entry(self.frame, font=Style.body, fg=Style.white, bg=Style.gray, width=40, bd=4)
        self.entry.place(x=20, y=50)
        # Main text frame
        self.text_main = tk.Text(self.frame, font=Style.head, fg=Style.white, bg=Style.gray, width=108, height=29)
        self.set_text_main()
        # Side text frame
        self.text_side = tk.Text(self.frame, font=Style.head, fg=Style.green_d, bg=Style.gray, width=33, height=29)
        self.set_text_side()
        # Buttons for links
        self.button_result = []
        self.button_similar = []

        # ID search button
        s_id = partial(self.search_id, table)
        self.button_id = tk.Button(self.frame, text="Search by id", font=Style.head,
                                   fg=Style.green_d, bg=Style.gray, command=s_id)
        self.button_id.place(x=575, y=48)

        # Name search button
        s_name = partial(self.search_name, table)
        self.button_name = tk.Button(self.frame, text="Search by name", font=Style.head,
                                     fg=Style.green_d, bg=Style.gray, command=s_name)
        self.button_name.place(x=712, y=48)

    def set_text_main(self):
        self.text_main.delete("1.0", tk.END)
        self.text_main = tk.Text(self.frame, font=Style.head, fg=Style.white, bg=Style.gray, width=90, height=29)
        self.text_main.tag_config("Heading", foreground=Style.green_l, background=Style.gray, font=Style.head)
        self.text_main.tag_config("Paragraph", foreground=Style.white, background=Style.gray, font=Style.body)
        self.text_main.place(x=20, y=100)
        return None

    def set_text_side(self):
        self.text_side.delete("1.0", tk.END)
        self.text_side = tk.Text(self.frame, font=Style.head, fg=Style.green_d, bg=Style.gray, width=45, height=29)
        self.text_side.place(x=1025, y=100)
        return None

    def set_button_result(self):
        for i in range(len(self.button_result)):
            self.button_result[i].destroy()
        self.button_result = []
        return None

    def set_button_similar(self):
        for i in range(len(self.button_similar)):
            self.button_similar[i].destroy()
        self.button_similar = []
        return None

    def search_id(self, b_table):
        try:
            this_buss = b_table[self.entry.get()]
            self.present_self(this_buss, b_table)
        except KeyError:
            self.set_text_main()
            self.set_text_side()
            self.set_button_result()
            self.set_button_similar()
            self.text_main.insert(tk.END, "Did not find anything :(\n", "Heading")
        return None

    def search_name(self, b_table):
        self.set_text_main()
        self.set_text_side()
        self.set_button_result()
        self.set_button_similar()
        user_input = self.entry.get()
        i = 0

        for key in b_table:
            if b_table[key].name == user_input:
                action = partial(self.present_self, b_table[key], b_table)
                info = b_table[key].name + " (" + b_table[key].city + ")"
                self.button_result.append(tk.Button(self.text_main, text=info, font=Style.head,
                                                    fg=Style.green_l, bg=Style.gray, command=action))
                self.button_result[i].pack()
                i += 1

        if i == 0:
            self.set_text_main()
            self.text_main.insert(tk.END, "No matching names :(\n", "Heading")
        return None

    def present_self(self, this_buss, b_table):
        # Clear out existing text and buttons
        self.set_text_main()
        self.set_text_side()
        self.set_button_result()
        self.set_button_similar()

        # Display name and city as title
        title = "\n" + this_buss.name + "\n\n"
        self.text_main.insert(tk.END, title, "Heading")

        # Display business information as paragraph
        info = "Address: " + this_buss.address + ", " + this_buss.city + ", "
        info = info + this_buss.state + ", " + this_buss.postal_code
        category = "Categories: {" + this_buss.categories + "}"
        self.text_main.insert(tk.END, info + "\n", "Paragraph")
        self.text_main.insert(tk.END, category, "Paragraph")

        # Find 10 most similar businesses
        most_sim = {}
        for key in b_table:
            if this_buss != b_table[key]:
                score = sim_score(this_buss, b_table[key])
            else:
                continue

            if len(most_sim) >= 10:
                key_min = min(most_sim.keys(), key=(lambda k: most_sim[k]))
                if score >= most_sim[key_min]:
                    del most_sim[key_min]
                    most_sim[key] = score
            else:
                most_sim[key] = score
        most_sim = dict(sorted(most_sim.items(), key=lambda item: item[1], reverse=True))

        # Display 10 most similar businesses
        i = 0
        for key in most_sim:
            action = partial(self.present_self, b_table[key], b_table)
            self.button_similar.append(tk.Button(self.text_side, text=b_table[key].name, font=Style.head,
                                                 fg=Style.green_l, bg=Style.gray, command=action))
            self.button_similar[i].pack()
            i += 1
        return None


if __name__ == '__main__':
    hashtable = {}
    hashtable = load_business(hashtable)
    hashtable = load_reviews(hashtable)

    # Save only the 10 most frequent word for each business
    for bus_key in hashtable:
        hashtable[bus_key].word_table = sort_word(hashtable[bus_key])

    # Show data
    root = tk.Tk()
    root.geometry("1600x800")
    BusinessesGUI(root, hashtable)
    root.mainloop()
