import re
import sys


# Function to parse attribute value conditions
def attr_value(conditions):
    data = {'in': [], "supseteqln": []}
    for i in conditions:
        if i == ' ' or i == '':
            continue
        if ' in ' in i:
            name, value = i.split(' in ')
            data['in'].append([name.strip(), value.strip()])
        elif ' supseteqln ' in i:
            name, value = i.split(' supseteqln ')
            data['supseteqln'].append([name.strip(), value.strip()])
        else:
            print("Condition not found: ", i)
    return data


# Function to parse attribute attribute conditions
def attr_attrib(conditions):
    data = {'<': [], ">": [], "=": [], "]": []}
    for i in conditions:
        if i == ' ' or i == '':
            continue
        if '<' in i:
            name, value = i.split('<')
            data['<'].append([name.strip(), value.strip()])
        elif '>' in i:
            name, value = i.split('>')
            data['>'].append([name.strip(), value.strip()])
        elif '=' in i:
            name, value = i.split('=')
            data['='].append([name.strip(), value.strip()])
        elif ']' in i:
            name, value = i.split(']')
            data[']'].append([name.strip(), value.strip()])
        else:
            print("Condition not found: ", i)
    return data


# Function to check attribute value conditions
def attr_value_check(data, element):
    for i in data['in']:
        if i[0] not in element:
            return False
        if element[i[0]] not in i[1]:
            return False
    for i in data['supseteqln']:
        if i[0] not in element:
            return False
        if not set(i[1]).issubset(set(element[i[0]])):
            return False
    return True


# Function to check attribute attribute conditions
def attr_attrib_check(data, user, resource):
    for i in data['<']:
        if i[0] not in user or i[1] not in resource:
            return False
        if not set(resource[i[0]]).issubset(set(user[i[1]])):
            return False
    for i in data['>']:
        if i[0] not in user or i[1] not in resource:
            return False
        if not set(user[i[0]]).issubset(set(resource[i[1]])):
            return False
    for i in data['=']:
        if i[0] not in user or i[1] not in resource:
            return False
        if user[i[0]] != resource[i[0]]:
            return False
    for i in data[']']:
        if i[0] not in user or i[1] not in resource:
            return False
        if resource[i[1]] not in user[i[0]]:
            return False
    return True


# Function to generate data to the visualisation
# the data is saved in data.txt
# the first line is the list of users (uid)
# the second line is the list of resources (rid)
# the third line is a dictionary of the form {(uid,rid):{operations}} it's corresponding of the authorization user/resource/operation
def gen_data(file_path):
    try:
        with open(file_path, 'r') as file:
            lines = file.readlines()
    except FileNotFoundError:
        print("File not found")
        exit(1)

    users = []
    resources = []
    rules = []

    for line in lines:
        rule = re.findall(r'rule\s*\((.*?)\)', line)
        if len(rule) == 1:
            rule = rule[0].split(';')
            data = {"name": rule[0]}
            user_conditions = rule[1].split(',')
            data['user'] = attr_value(user_conditions)
            resource_conditions = rule[2].split(',')
            data['resource'] = attr_value(resource_conditions)
            operations = rule[3].split('{')[1].split('}')[0].split(' ')
            data['operations'] = operations
            resource_user_conditions = rule[4].split(',')
            data['resource_user'] = attr_attrib(resource_user_conditions)
            rules.append(data)
        user = re.findall(r'userAttrib\s*\((.*?)\)', line)
        if len(user) == 1:
            user = user[0].split(',')
            data = {'uid': user[0]}
            user = user[1:]
            for i in user:
                data[i.split('=')[0].strip()] = i.split('=')[1].strip()
            users.append(data)
        resource = re.findall(r'resourceAttrib\s*\((.*?)\)', line)
        if len(resource) == 1:
            resource = resource[0].split(',')
            data = {'rid': resource[0]}
            resource = resource[1:]
            for i in resource:
                data[i.split('=')[0].strip()] = i.split('=')[1].strip()
            resources.append(data)

    output = {}
    for rule in rules:
        user_verified = []
        for user in users:
            if attr_value_check(rule['user'], user):
                user_verified.append(user)
        resource_verified = []
        for resource in resources:
            if attr_value_check(rule['resource'], resource):
                resource_verified.append(resource)
        for user in user_verified:
            for resource in resource_verified:
                if attr_attrib_check(rule['resource_user'], user, resource):
                    output[(user['uid'], resource['rid'])] = set(rule['operations'])
    users_ = [i['uid'] for i in users]
    resources_ = [i['rid'] for i in resources]
    with open('abac_res.txt', 'w') as file:
        file.write(str(users_) + '\n')
        file.write(str(resources_) + '\n')
        file.write(str(output))


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python3 abac_reader.py <file>")
        exit(1)
    gen_data(sys.argv[1])
