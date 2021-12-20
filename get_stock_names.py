import praw
import pandas as pd 

# requires a Reddit account and developer App
username = 'steve55677'
password = 'dickface1'
userAgent = 'wsbscraper' # can be random string
clientId = 'ouT0A38wSJwpaQ'
secretKey = 'CYkJCA_osUfnYxEX8jZKFMaJrCaH5g'

# enter chcp 65001 on cmd prompt to resolve charmap isssues on windows

def getData():
    '''
    uses the reddit api to get information from r/wallstreetbets
    '''
    # create reddit instance with OAuth2
    reddit = praw.Reddit(client_id = clientId, client_secret = secretKey , username=username, password=password, user_agent=userAgent)
    subreddit = reddit.subreddit('wallstreetbets')
    trending_topics = list(subreddit.hot(limit=None))
    potential_stock_names = [] 
    trending_stock_names =  []
    stock_names_list = pd.read_csv('stock-names-sheet.csv')['Name'].tolist()
    full_stock_names_list = pd.read_csv('stock-names-sheet.csv')['FullName'].tolist()
    d =  {"Name": stock_names_list,  "FullName": full_stock_names_list  }
    stock_df = pd.DataFrame(d)
    stock_df['Name'] = stock_df['Name'].astype('|S')

    for topic in trending_topics:
        # ex :"Daily Popular Tickers Thread for June 16, 2021 - AMC | CLNE | DKNG"    
        # assuming stock names are 1 - 5 characters long, and all caps
        headline = topic.title 
        for i in range(len(headline)):
            try:
                currentCharacterSelection = headline[i:i+5].replace(" ", "")            
                if(currentCharacterSelection.isupper() and currentCharacterSelection.isalnum()):
                    if currentCharacterSelection in stock_names_list:
                        trending_stock_names.append(currentCharacterSelection)
            except:
                pass

    trending_stock_names = list(set(trending_stock_names)) # eliminate duplicates
    trending_stocks_rank =  {}

    for stock in trending_stock_names:
        trending_stocks_rank[stock] = {'comments': 0, 'upvote_ratio':0, 'score':0, 'downs':0, "ups": 0, "headlines": []}  

    # ex of trending stocks =   { AMC: {comments: y, upvotes: x } }
    # rank trending stock names based on engagement
    # we are assuming that the higher a upvote ratio and score
    # the higher ranking the stock, or more upside potential for stock gains

    for stock in trending_stock_names:
        for post in trending_topics:
            headline = post.title            
            if stock in headline:
                previousScoreCard = trending_stocks_rank[stock]
                new_comments = previousScoreCard['comments'] + len(post.comments)
                new_upvote_ratio = previousScoreCard['upvote_ratio'] + post.upvote_ratio
                new_score = previousScoreCard['score']  + post.score
                new_ups = previousScoreCard['ups'] + post.ups
                new_downs = previousScoreCard['downs'] + post.downs
                previous_headlines = previousScoreCard['headlines']                
                head_line_dict = {"headline": post.title, "url": post.url}                          
                previous_headlines.append(head_line_dict)
                new_headlines = previous_headlines
                newScoreCard = {}

                encoded_name = stock.encode('utf-8')
                full_row =  stock_df.loc[stock_df['Name'] == encoded_name]
                full_name =  list(full_row['FullName'])[0]

                newScoreCard['company_name'] = full_name
                newScoreCard['comments']  = new_comments
                newScoreCard['upvote_ratio']  = new_upvote_ratio
                newScoreCard['score']  = new_score
                newScoreCard['tickerName'] = stock
                newScoreCard['ups'] = new_ups
                newScoreCard['downs'] = new_downs
                newScoreCard['headlines'] = new_headlines
                trending_stocks_rank[stock] = newScoreCard 
    # list of dict
    stock_object_list = []
    
    def insertion_sort_impl(L, *, key):
        # loop-invariant: `L[:i]` is sorted
        for i in range(1, len(L)):
            d = L[i]
            for j in range(i - 1, -1, -1): 
                if key(L[j]) <= key(d): 

                     break
                L[j + 1] = L[j]
            else: 
                j -= 1
            L[j + 1] = d

    for stock in trending_stocks_rank:       
        encoded_name = stock.encode('utf-8')
        full_row =  stock_df.loc[stock_df['Name'] == encoded_name]
        full_name =  list(full_row['FullName'])[0]
        new_stock_dict = {}
        raw_stock_object = trending_stocks_rank[stock]
        # raw_stock_object['full_name'] = full_name     
        new_stock_dict[full_name] = raw_stock_object     
        stock_object_list.append(new_stock_dict)

    # sort by `d` key
    insertion_sort_impl(stock_object_list, key=lambda x:  x[list(x.keys())[0]]['score']) 
    stock_object_list.reverse()
    return stock_object_list    
        
def print_to_excel(stock_data):
    summary_df = pd.DataFrame()

    for i in range(len(stock_data)):
        for key in stock_data[i]:
            summary_df = summary_df.append(stock_data[i][key], ignore_index=True)

    with pd.ExcelWriter('wsb_simplified.xlsx') as writer:
        summary_df.to_excel(writer, index=False, sheet_name='ranks')
        for stock in stock_data:
            current_stock_name = list(stock.keys())[0]
            headline_list = stock[current_stock_name]['headlines']
            headline_name_column_list = []
            headline_url_column_list = []

            for headline_object in headline_list:
                headline_name = headline_object['headline']
                headline_url = headline_object['url']
                headline_name_column_list.append(headline_name)
                headline_url_column_list.append(headline_url)
            current_stock_df = pd.DataFrame(list(zip(headline_name_column_list, headline_url_column_list)),columns =['Post Name', 'Post URL'])  
            current_stock_df.reset_index()
            current_stock_df.to_excel(writer, index=False, sheet_name=current_stock_name[0:29])

if __name__ == "__main__":
    stock_data_array = getData()
    print_to_excel(stock_data_array)