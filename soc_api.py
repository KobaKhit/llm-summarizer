import praw
from datetime import datetime
import os
import csv
from tqdm import tqdm
from urllib.parse import urlparse
import itertools
import sys


class Reddit():
    def __init__(self, client_id, client_secret):

        # initialize praw instance
        self.session = self.reddit_auth(client_id, client_secret)


    def reddit_auth(self, client_id = None, client_secret = None):
        '''
        Initialize PRAW instance
        '''
        cid = client_id
        cse = client_secret
            
        reddit = praw.Reddit(
            client_id=cid,
            client_secret=cse,
            user_agent="Downloading comments"
        )
        
        return reddit

    @staticmethod
    def parse_submission(sub):
        '''
        Parse PRAW Submission (Thread) object
        '''
        res={}
        fields = ['id','author','title','selftext','url',
                    'created_utc','subreddit',
                    'score','permalink',
                    'distinguished','upvote_ratio','subreddit']
        
        for f in fields:
            res[f] = sub.__getattribute__(f)

        res['url_domain'] = urlparse(res['url']).netloc
        res['created_date'] = datetime.utcfromtimestamp(res['created_utc']) 
        res['type'] = 'submission'
        res['submission_id'] = res['id']
        res['submission_text'] = res.pop('selftext')

        return res 
    

    @staticmethod
    def parse_comment(com):
        '''
        Parse PRAW Comment object
        '''
        res = {}
        fields = ['id','author','body',
                    'created_utc','parent_id','link_id',
                    'score','num_reports','controversiality',
                    'gilded','downs','likes','permalink',
                    'total_awards_received','subreddit']
        for f in fields:
            res[f] = com.__getattribute__(f) 

        res['author'] = res['author'].name if res['author'] != None else None
        res['created_date'] = datetime.utcfromtimestamp(res['created_utc']) 
        res['type'] = 'comment' if res['parent_id'].split('_')[0] =='t3' else 'comment_reply'
        res['submission_id'] = res.pop('link_id').split('_')[1]
        
        return res
    
    def get_submissions(self, subreddit,time_filter='day', limit=1000):
        '''
        Get Top Submission (Threads/Posts) ids from a given subreddit.
        '''
        reddit = self.session# auth
        posts = reddit.subreddit(subreddit).top(time_filter=time_filter, limit=limit)
        return [p.id for p in posts]

    def process_submissions(self, URL, verbose=False):
        '''
        Scrape comments from reddit thread (submission) URL
        '''
      
        reddit = self.session # auth
        retrieve_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if type(URL) == list:
            ret = []
            for u in tqdm(URL):
                ret += self.process_submissions(u)
            return ret

        params = {'url': URL}
        if 'reddit.com' not in URL: params['id'] = params.pop('url')
        submission = reddit.submission(**params)
        submission.comments.replace_more(limit=None)

        # collect and parse thread and thread comments
        sub_parsed = self.parse_submission(submission) # get thread submission first
        sub_parsed['retrieve_time'] = retrieve_time
        comment_list = [sub_parsed] # submission dict guaranteed to be first element

        # collect thread comments
        for comment in submission.comments.list():
            com_parsed = self.parse_comment(comment)
            com_parsed['retrieve_time'] = retrieve_time
            comment_list.append(com_parsed)

        # print summary
        if verbose:
            summary_string = f'Downloaded {len(comment_list)} comments from \n{URL}'
            print(summary_string, end='\r')
        return comment_list

    @staticmethod
    def write_csv(to_csv, filename=None):
        '''
        Save list of dictionaries as a csv file
        '''
        if filename == None:
            filename = f'./downloaded-comments/comments-{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}.csv'

            # create folder if does not exist
            os.makedirs(os.path.dirname(filename), exist_ok=True)

        keys = set(itertools.chain.from_iterable([d.keys() for d in to_csv[0:2]]))
        
        with open(filename, 'w', newline='') as output_file:
            dict_writer = csv.DictWriter(output_file, keys)
            dict_writer.writeheader()
            dict_writer.writerows(to_csv)

def main():
    pass

if __name__=='__main__':
    main()


  