# CSC 365 Assignment 3
# For each business, find 4 geographically closest business.
# Report the number of disjoint sets from previous step.
# Serialize both into file
import json
import random
from math import radians, sin, cos, sqrt, asin


# For each business, assign 4 closest businesses, then write into file.
def calculate_closest(data, file_name):
    print("Calculating closest businesses...")
    counter = 0

    result = {}
    # Make two sorted list for scope management, takes too long to calculate everything
    sort_by_lat = sorted(data, key=(lambda x: data[x]['latitude']))
    sort_by_lon = sorted(data, key=(lambda x: data[x]['longitude']))

    for id_this in data:
        closest = {}
        close_lat = limit_scope(sort_by_lat, id_this)
        close_lon = limit_scope(sort_by_lon, id_this)

        # Find closest businesses from businesses with closest latitude.
        for id_other in close_lat:
            if id_this != id_other:
                distance = calculate_distance(data, id_this, id_other)
                closest[id_other] = distance

            # Only keep 4 closest businesses
            if len(closest) == 5:
                furthest = max(closest.keys(), key=(lambda k: closest[k]))
                del closest[furthest]

        # Find closest businesses from businesses with closest longitude.
        for id_other in close_lon:
            if id_this != id_other:
                distance = calculate_distance(data, id_this, id_other)
                closest[id_other] = distance

            # Only keep 4 closest businesses
            if len(closest) == 5:
                furthest = max(closest.keys(), key=(lambda k: closest[k]))
                del closest[furthest]

        # Only the ids of the closest businesses are saved
        keys = []
        for each in closest:
            keys.append(each)
        result[id_this] = keys

        counter += 1
        if counter == 5000:
            print("Closest businesses found x5000")
            counter = 0

    with open(file_name, 'w') as file:
        json.dump(result, file, indent=4)
        file.close()
        print("Closest businesses calculated")
    return None


# Calculate the disjoint sets, then write into file
def calculate_disjoint_sets(data, file):
    print("Calculating disjoint sets...")
    disjoint_sets = {}                  # Try to make disjoint sets a hash table for easier management
    counter = 0

    for b_id in data:
        for link in data[b_id]:
            exist_id = check_in_sets(b_id, disjoint_sets)
            exist_link = check_in_sets(link, disjoint_sets)
            if exist_id:
                if exist_link:
                    # This id and link both already in disjoint sets
                    key_id = find_key(disjoint_sets, b_id)
                    key_link = find_key(disjoint_sets, link)
                    if key_id == key_link:
                        # Both id and link already exist in the same disjoint set
                        continue
                    else:
                        # Join up the 2 sets/lists, delete the second one
                        disjoint_sets[key_id] = disjoint_sets[key_id] + disjoint_sets[key_link]
                        del disjoint_sets[key_link]
                else:
                    # This id is in the disjoint set but it's link is not
                    key_id = find_key(disjoint_sets, b_id)
                    disjoint_sets[key_id].append(link)
            else:
                if exist_link:
                    # This business is not in disjoint set but it's link is, add business into link's set/list
                    key_link = find_key(disjoint_sets, link)
                    disjoint_sets[key_link].append(b_id)
                else:
                    # Neither this business nor it's link exist in the disjoint set, make a new set for them
                    new_key = find_new_key(disjoint_sets)
                    disjoint_sets[new_key] = [b_id, link]

        counter += 1
        if counter == 1000:
            print("1000 Businesses processed...")
            counter = 0

    with open(file, 'w') as f:
        json.dump(disjoint_sets, f, indent=4)
        print("Disjoint sets calculated")
        f.close()

    return None


# Calculate the distance between 2 businesses using haversine formula.
def calculate_distance(data, b_this, b_other):
    # Angle = Distance / Radius
    r = 6371
    lat1 = data[b_this]['latitude']
    lat2 = data[b_other]['latitude']
    lon1 = data[b_this]['longitude']
    lon2 = data[b_other]['longitude']

    d_lat = radians(lat2 - lat1)
    d_lon = radians(lon2 - lon1)
    lat1 = radians(lat1)
    lat2 = radians(lat2)

    a = sin(d_lat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(d_lon / 2) ** 2
    c = 2 * asin(sqrt(a))

    return r * c


# Check if a business id is already in the disjoint sets
def check_in_sets(b_id, disjoint_sets):
    for each in disjoint_sets:
        if b_id in disjoint_sets[each]:
            return True
    return False


# Find all the links that b_id have, then return it in a list
def find_all_links(data, b_id):
    new_list = [b_id]
    for element in new_list:
        for link in data[element]:
            if link not in new_list:
                new_list.append(link)
            else:
                continue
    return new_list


# Find the key to which the id resides
def find_key(sets, b_id):
    for key in sets:
        if b_id in sets[key]:
            return key
    return None


# Find a new name to use for the disjoint set
def find_new_key(sets):
    keys_exist = []
    for key in sets:
        keys_exist.append(key)

    while True:
        new_key = "disjoint_set_" + str(random.randint(0, 199999))
        if new_key not in keys_exist:
            return new_key


# Read businesses in file, return a dictionary that includes their ids, latitude, and longitude.
def get_locations(file_name):
    print("Loading business locations from file...")

    data = {}
    with open(file_name, 'r', encoding="utf-8") as file:
        for line in file:
            entity = json.loads(line)
            if entity['is_open'] == 1:
                b_id = entity['business_id']
                latitude = entity['latitude']
                longitude = entity['longitude']
                data[b_id] = {'latitude': latitude, 'longitude': longitude}
    file.close()

    print("Business locations loaded from file.")
    return data


# Return a list of (at most) 50 business ids that are before the index
def get_lower_scope(sorted_list, index):
    smaller_list = []
    if index < 50:
        for i in range(index):
            smaller_list.append(sorted_list[i])
    else:
        for i in reversed(range(50)):
            smaller_list.append(sorted_list[index - i])
    return smaller_list


# Return a list of (at most) 50 business ids that are after the index
def get_higher_scope(sorted_list, index):
    smaller_list = []
    if index > len(sorted_list) - 50:
        for i in range(len(sorted_list) - index):
            smaller_list.append(sorted_list[i + index])
    else:
        for i in range(50):
            smaller_list.append(sorted_list[i + index])
    return smaller_list


def limit_scope(sorted_list, b_id):
    index = sorted_list.index(b_id)
    lower_scope = get_lower_scope(sorted_list, index)
    higher_scope = get_higher_scope(sorted_list, index)
    return lower_scope + higher_scope


def load_closest(file):
    print("Loading closest businesses...")
    with open(file, 'r') as f:
        data = json.load(f)
        f.close()
    print("Closest businesses loaded.")
    return data


if __name__ == '__main__':
    locations = get_locations("yelp_academic_dataset_business.json")
    calculate_closest(locations, "closest_businesses.json")
    closest_b = load_closest("closest_businesses.json")
    calculate_disjoint_sets(closest_b, "disjoint_sets.json")
