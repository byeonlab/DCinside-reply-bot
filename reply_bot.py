'''
Created on 2016. 11. 25.

@author: BYJ
'''
import re
from selenium import webdriver
import bs4
import lxml
import urllib
import scrapy
import datetime
import time
import json

def remove_repetition(List,i,result):
    if  i<len(List):
        if List[i] in result:
            return remove_repetition(List,i+1,result) 
        return remove_repetition(List,i+1,result+List[i:i+1])
    return result

def get_post_lists(post_nums,i,List):
    if i< len(post_nums):
        return get_post_lists(post_nums,i+1,List+[post_nums[i].get_text(strip=True)])
    return ascend_sort(List,0,[],[],[])

def ascend_sort(List,i,smaller,pivot,greater):
    if 1<len(List):
        if i<len(List):
            if List[i]>List[len(List)-1]:
                return ascend_sort(List,i+1,smaller,pivot,greater+List[i:i+1])
            if List[i]==List[len(List)-1]:
                return ascend_sort(List,i+1,smaller,pivot+List[i:i+1],greater)
            if List[i]<List[len(List)-1]:
                return ascend_sort(List,i+1,smaller+List[i:i+1],pivot,greater)
            return ascend_sort(List,i+1,smaller,pivot,greater)
        return ascend_sort(smaller,0,[],[],[])+pivot+ascend_sort(greater,0,[],[],[])
    return List

def grammar_correction(texts,memo_area,send_button,reciever):
    output1=re.findall(r"안되 |안되|되서|되도(?=^록)",texts)
    output2=re.findall(r"됬",texts)
    _output1=remove_repetition(output1,0,[])
    _output2=remove_repetition(output2,0,[])
    
    for element in _output1:
        memo_area.send_keys("%s//"%reciever+"'%s' ->"%element+" '%s'"%element.replace('되','돼')+" [문법나치]")
        send_button.click()
        print ("---댓글 작성함")
        time.sleep(10)
    
    for element in _output2:
        memo_area.send_keys("%s//"%reciever+"'됬' -> '됐' [문법나치]")
        send_button.click()
        print ("---댓글 작성함")
        time.sleep(10)


def get_title_text(driver):
    title=driver.find_element_by_class_name('wt_subject')
    _content=title.find_element_by_tag_name("dd")
    content_text=_content.text
    #grammar_correction(content_text, memo_area, send_button,"제목")
    return content_text
            
def get_post_text(driver):

    post=driver.find_element_by_class_name('s_write')
    _content=post.find_element_by_tag_name("td")
    content_text=_content.text
    #grammar_correction(content_text, memo_area, send_button,"본문")
    return content_text

def get_reply_lines(driver,nicks,comments,times):
    nicks=[]
    comments=[]
    times=[]
    
    for row in driver.find_elements_by_css_selector("tr.reply_line"):
        nick= row.find_elements_by_tag_name("td")[0]
        comment= row.find_elements_by_tag_name("td")[1]
        time= row.find_elements_by_tag_name("td")[2]
        nicks.append(nick.text)
        comments.append(comment.text)
        times.append(time.text)
        
    return nicks,comments,times
        
def reply_check(driver,memo_area,send_button,_index,id,reply_log):
    _nicks,_comments,_times=[],[],[]
    nicks,comments,times=get_reply_lines(driver,_nicks,_comments,_times)

    for j in range (len(comments)):
        if datetime.datetime.strptime(times[j],'%Y.%m.%d %H:%M:%S')>datetime.datetime.strptime(reply_log["%s"%_index],'%Y.%m.%d %H:%M:%S'):
            if nicks[j]!="문법나치":
                grammar_correction(str(comments[j]), memo_area,send_button,str(nicks[j]))
        update_log(reply_log,"%s"%_index,datetime.datetime.strptime(times[j],'%Y.%m.%d %H:%M:%S').strftime("%Y.%m.%d %H:%M:%S"))
        save_log(id,'reply',reply_log)

            
def iterate_posts(_index,reply_log,post_log,title_log,id):
    driver=webdriver.PhantomJS()
    for i in range(len(_index)):
        print ("게시글 %s번 시작"%_index[i])
        url="http://gall.dcinside.com/board/view/?id=%s"%id+"&no=%s"%_index[i]
        try:

            driver.get(url)
            driver.find_element_by_id("name").send_keys("문법나치")
            driver.find_element_by_id("password").send_keys("1111")
            memo_area=driver.find_element_by_id("memo")
            send_button=driver.find_element_by_xpath('//img[contains(@src,"http://nstatic.dcinside.com/dgn/gallery/images/btn_re_1.gif")]')
                   
            if title_log[_index[i]]=="false":
                try:    
                    grammar_correction(get_title_text(driver), memo_area, send_button,"제목")
                    title_log[_index[i]]="true"
                    save_log(id,'title',title_log)
                except:
                    pass
            if post_log[_index[i]]=="false":
                try:
                    grammar_correction(get_post_text(driver), memo_area, send_button,"본문")
                    post_log[_index[i]]="true"
                    save_log(id,'post',post_log)
                except:
                    pass
            reply_check(driver,memo_area,send_button,_index[i],id,reply_log)      
 
            print ("게시글 %s번 완료"%_index[i])
        
        except:
            pass
    driver.quit()


def get_log(id,args):
    try:
        with open('/Users/yj/Desktop/developpe/jijin/src/%s'%id+'_%s_log.json'%args) as file:    
            log = json.load(file)
        file.close()
    except:
        log={}

    return log

def save_log(id,args,log):
    with open('/Users/yj/Desktop/developpe/jijin/src/%s'%id+'_%s_log.json'%args, 'w') as file:
        json.dump(log, file)
    file.close()

def update_log(log,key,value):
    log[key]=value
 

if __name__=="__main__":

    id=input("갤러리 id값을 입력하세요: ")
    

    reply_log=get_log(id,'reply') 
    post_log=get_log(id,'post')
    title_log=get_log(id,'title')

    
    while (1):

        #post_times=parsed.find_all('td',class_='t_date')

        gallery=urllib.request.urlopen('http://gall.dcinside.com/board/lists/?id=%s'%id)
        parsed=bs4.BeautifulSoup(gallery,'lxml')
        post_nums=parsed.find_all('td', class_='t_notice')

        _index=get_post_lists(post_nums,0,[])
        print (_index)
        
        for i in range(len(_index)):
            print (_index[i])
            if _index[i] not in reply_log:
                update_log(reply_log,_index[i],datetime.datetime(1,1,1,0,0,0).strftime("%Y.%m.%d %H:%M:%S"))
            if _index[i] not in post_log:
                update_log(post_log,_index[i],"false")
            if _index[i] not in title_log:
                update_log(title_log,_index[i],"false")
        
        save_log(id,'reply',reply_log)
        save_log(id,'post',post_log)
        save_log(id,'title',title_log)

        iterate_posts(_index,reply_log,post_log,title_log,id)
