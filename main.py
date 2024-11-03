import requests
import csv
import time

#hashed out my access token
# i used a rate limit function prior to using my access token, i've left my rate limit consideration in the code
TOKEN = '******'  

#USERS.CSV
#rate limit consideration added/ before gettin my token
def get_user_data(user_login):
    user_url = f"https://api.github.com/users/{user_login}"
    headers = {'Authorization': f'token {TOKEN}'}
    user_response = requests.get(user_url, headers=headers)

    if user_response.status_code == 200:
        return user_response.json()
    elif user_response.status_code == 429:
        reset_time = int(user_response.headers.get("X-RateLimit-Reset"))
        wait_time = reset_time - int(time.time()) 
        print(f"Rate limit exceeded. Waiting for {wait_time} seconds.")
        time.sleep(wait_time)
        return get_user_data(user_login) #not required after token
    else:
        print(f"Failed to fetch user data for {user_login}: {user_response.status_code}")
        return None

#my base URL for the GitHub API to search users
base_url = "https://api.github.com/search/users?q=location:Boston+followers:>100&per_page=100"
#headers for authentication
headers = {'Authorization': f'token {TOKEN}'}

users = []
#paeination
page = 1
while True:   
    url = f"{base_url}&page={page}"    
    #GET request to the API
    response = requests.get(url, headers=headers)
    # Check success
    if response.status_code == 200:
        data = response.json()      
        #when no more users, break the loop
        if not data['items']:
            break

        #collect user information
        for user in data['items']:
            user_data = get_user_data(user['login'])  # Use the function to get user data
            if user_data:
                #cleaning up company field
                company = user_data.get('company', '')
                if company:
                    #trim whitespace, remove leading '@' if it exists, and convert to uppercase
                    company = company.strip().lstrip('@').upper()

                users.append({
                    'login': user_data['login'],
                    'name': user_data.get('name', ''),
                    'company': company,
                    'location': user_data.get('location', ''),
                    'email': user_data.get('email', ''),
                    'hireable': user_data.get('hireable', ''),
                    'bio': user_data.get('bio', ''),
                    'public_repos': user_data.get('public_repos', 0),
                    'followers': user_data['followers'],
                    'following': user_data.get('following', 0),
                    'created_at': user_data['created_at'],
                })
                #pause to avoid hitting API rate limits/ pre token
                time.sleep(1)
        #incrementing the page number for the next request
        page += 1
        
    elif response.status_code == 429:  # Handle rate limit
        reset_time = int(response.headers.get("X-RateLimit-Reset"))
        wait_time = reset_time - int(time.time())  # Calculate wait time
        print(f"Rate limit exceeded. Waiting for {wait_time} seconds.")
        time.sleep(wait_time)
    else:
        print(f"Error: {response.status_code}")
        break
#write data to users.csv
if users:
    with open('users.csv', mode='w', newline='', encoding='utf-8') as csv_file:
        fieldnames = users[0].keys()
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(users)

    print(f"Saved {len(users)} users to users.csv.")
else:
    print("No users found matching the search criteria.")



#SEPERATE FILE WAS MADE, but i added it to this for convenience
#REPOSITORIES.CSV 
#added rate limit consideration before authentication token
def get_repositories(user_login):
    repos_url = f"https://api.github.com/users/{user_login}/repos?per_page=100"
    headers = {'Authorization': f'token {TOKEN}'}
    all_repositories = []
    page = 1

    while True:
        #constructing the URL for the current page
        url = f"{repos_url}&page={page}"
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            repos_data = response.json()
            if not repos_data:  
                break

            #sorting repositories by pushed_at (latest pushed first)
            #repos_data.sort(key=lambda x: x.get('pushed_at', ''), reverse=True) didn't work accurately
            repos_data.sort(key=lambda x: x.get('pushed_at', '1970-01-01T00:00:00Z') or '1970-01-01T00:00:00Z', reverse=True)

            all_repositories.extend(repos_data)

            #incrementing the page number for the next request
            page += 1
        elif response.status_code == 429:
            reset_time = int(response.headers.get("X-RateLimit-Reset"))
            wait_time = reset_time - int(time.time())  # Calculate wait time
            print(f"Rate limit exceeded. Waiting for {wait_time} seconds.")
            time.sleep(wait_time)
        else:
            print(f"Error: {response.status_code}")
            break

    #returning only the first 500 repositories
    return all_repositories[:500]  

#read users from users.csv
with open('users.csv', mode='r', encoding='utf-8') as csv_file:
    csv_reader = csv.DictReader(csv_file)
    repositories = []

    for user in csv_reader:
        user_login = user['login']
        print(f"Fetching repositories for {user_login}...")
        user_repos = get_repositories(user_login)

        for repo in user_repos:
            repositories.append({
                'login': user_login,
                'full_name': repo['full_name'],
                'created_at': repo['created_at'],
                'stargazers_count': repo['stargazers_count'],
                'watchers_count': repo['watchers_count'],
                'language': repo['language'],
                'has_projects': repo.get('has_projects', False),
                'has_wiki': repo.get('has_wiki', False),
                'license_name': repo['license']['name'] if repo['license'] is not None else 'None'

            })

        #avoid hitting API rate limits
        time.sleep(1)

#writing repository data to repositories.csv
if repositories: 
    with open('repositories.csv', mode='w', newline='', encoding='utf-8') as csv_file:
        fieldnames = repositories[0].keys()
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(repositories)

    print(f"Saved {len(repositories)} repositories to repositories.csv.")
else:
    print("No repositories found for the users.")

