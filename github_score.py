import urllib2
import json
import sys
import base64

REPOSITORY_LIMIT = 500 # Check API Calls section in main docstring before editing
USER = "username"
OAUTH_TOKEN = "your token"

"""
Queries a github API URI and decodes the JSON response, or handles HTTP Errors
Uses USER/OAUTH from top of file

Usage:
url - a github api url

Return:
json data if successful
None if unsuccessful
"""
def api_call(url):
    try:
        req = urllib2.Request(url, headers={"Accept" : "application/vnd.github.preview"})
        base64string = base64.encodestring('%s:%s' % (USER, OAUTH_TOKEN))[:-1]
        req.add_header("Authorization", "Basic %s" % base64string)
        response = urllib2.urlopen(req)
        return json.load(response)
        return None

    except urllib2.HTTPError as msg:
        if msg.code == 403:
            print("403 Error, you've likely exceeded your api call limit")
        else:
            print(msg.code)

        return None
 
"""
Checks top x repos, x specified by limit, ordered by # of stars, and scores them
Score is as follows:
    1 point for each star
    2 points for each commit this year
    -1 point for every 5 open issues
    formula: stars + (2 * commits_this_year) - open_issues/5

    This lends a stronger weight to repositories that are both very popular AND 
    very active currently, causing some of the older, less active, established 
    repositories to not sit on top as easily.

API Calls
This method makes 1 api call per 100 repositories + 2 more for each repository
formula: CEILING(repositories/100) + (2 * repositories)
example: 350 repos scanned == 4 + 2*350 = 704 API calls
IMPORTANT: Github search supports a maximum of 1000 results

Big O
This function is O(num_repos).
Reasoning: 
    The function iterates once per 100 repos
    After this is complete it iterates once per repo
        within this it makes two API calls
        loops through top 5
"""
def main(limit = REPOSITORY_LIMIT): 
    top = [] # Stores top 5 scores
    repositories = [] # JSON blob of repositories
    pages = -( -limit // 100 ) + 1 # ceiling(limit/100) + 1

    # Add together pages of results
    # Github limits to 100 results per page
    for x in range(1, pages):
        ret = api_call(
            "https://api.github.com/search/repositories?q=stars:>=150&sort=stars&per_page=100&page=%d" % x)
        if ret == None:
            break
        else: 
            repositories += ret['items']

    # If there's a problem making the call
    if repositories == None: 
        print("Could not get repository list. Exiting")
        return

    for repo in repositories[:limit]:
        print('URL: %s') % repo['html_url']

        info = api_call(repo['url'])
        
        if info == None:
            continue # let's skip this one

        # Get number of people who have starred this repo
        # for some reason it's called watchers_count
        stars = int(info['watchers_count']) 

        # Get the number of open_issues for this repo
        open_issues = int(info['open_issues_count'])

        # Get the last year of commits
        commits = api_call(repo['url']+'/stats/commit_activity')
        if commits == None: # Something went wrong
            continue

        total_commits = 0
        for week in commits:
            total_commits += int(week['total'])
        
        score = stars + 2*total_commits - open_issues/5

        print('Stars: %s, Issues: %s, Commits: %s, Score: %s') % (
            stars,open_issues,total_commits, score)

        # Insert into the top 5, a list of (score, url) pairs
        # If there's not 5 top values, just append it
        if len(top) < 5: 
            top.append( (score, repo['html_url']) )
        else: 
            # Get the smallest of the top 5
            lowest = None
            for idx,score_pair in enumerate(top): 
                if lowest == None or top[lowest][0] > score_pair[0]:
                    lowest = idx

            # If it's the smallest is smaller than the current score, replace it
            if top[lowest][0] < score:
                top[lowest] = (score, repo['html_url'])

    print top


if __name__ == "__main__":
    main()