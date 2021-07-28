# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions


# This is a simple example for a custom action which utters "Hello World!"

import datetime
import traceback

from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, ReminderScheduled, ReminderCancelled

from QuerySearcher import QuerySearcher
from scrapper import  get_articles, get_sub_header, get_all_articles, get_file_url


menu_btn = {"title":"Hasierako menura itzuli", "payload":"/show_menu"}
articles_btn = {"title":"Artikuluen zerrenda erakutsi", "payload":"/show_news_menu"}
topics = ['Azken berriak', 'Berri irakurrienak', 'Gizartea', 
            'Politika', 'Ekonomia', 'Mundua', 'Iritzia', 'Kultura', 'Kirola', 'Bizigiro']


def send_articles(dispatcher, article_topic, show_next_news = False):
    '''
    Gets all the articles of the selected topic, sends them to the user and creates
    a menu with buttons.

    Parameters:
        - dispatcher (CollectingDispatcher): Last instance of the CollectingDispatcher object
        - article_topic (String): Topic chosen by the user
        - show_next_news (Boolean): Whether if articles are shown by user's innactivity or not

    Returns:
        - Events of the set slots
    '''

    events = []

    # Get the url of the topic html file
    url = get_file_url(article_topic)

    last_news = article_topic == 'Azken berriak'

    # Store the headers and their url in a list
    global_articles = get_articles(url, last_news)

    buttons = []

    # Create the message and the buttons menu that will be displayed
    message = "Artikuluen arloa: " + article_topic + "\n  \n"
    for article in global_articles.keys():
        message += article + "\n \n"
        entity = article.replace(" artikulua", "")
        btn = {"title":article, 
              "payload":"/choose_news_with_keywords{\"article\":" + entity + "}"}
        buttons.append(btn)

    buttons.append(menu_btn)

    if show_next_news:
        next_news_button = {"title":"Ez bidali mezu gehiago", "payload":"/cancel_show_news_reminder"}
        buttons.append(next_news_button)
    

    dispatcher.utter_message(text = message, buttons=buttons, button_type="reply")

    events.append(SlotSet('topic', article_topic))
    events.append(SlotSet('global_articles', global_articles))

    return events


def get_next_topic(tracker):
    '''
    Returns the next topic depending on the predefined priority. In order to maintain the list,
    in a circular order, the element removed from the begining of the list is appended to the end
    of it.

    Returns:
        - Next topic of the list 
    '''

    topics = tracker.get_slot('topic_list')
    topic = topics.pop(0)
    topics.append(topic)

    return topic, SlotSet('topic_list', topics)

class ActionAnswerOpenQuestion(Action):

    def name(self) -> Text:
        return "action_answer_open_question"

    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
    
        '''
        Prepares the chatbot to receive an open question
        '''

        dispatcher.utter_message(response="utter_answer_to_open_question_request")

        return [SlotSet('open_question', True)]

class ActionCancelNewsReminder(Action):

    def name(self) -> Text:
        return "action_cancel_news_reminder"

    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:

        '''
        Cancels all the scheduled reminders
        '''

        return [SlotSet('read_next_news', False), ReminderCancelled()]


class ActionSetNewsReminder(Action):

    def name(self) -> Text:
        return "action_set_news_reminder"

    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:

        '''
        Creates a reminder to show the articles of a topic when user is innactive.
        Articles will be shown every 15 seconds if the user does not send any message.
        '''

        read_next_news = tracker.get_slot('read_next_news')

        if read_next_news:

            date = datetime.datetime.now() + datetime.timedelta(seconds =  15)
            entities = tracker.latest_message.get('entities')

            reminder = ReminderScheduled(
                "EXTERNAL_reminder",
                trigger_date_time=date,
                entities=entities,
                name="my_reminder",
                kill_on_user_message=True,
            )

            return [reminder]

        else:

            return []


class ActionReactReminder(Action):

    def name(self) -> Text:
        return "action_react_reminder"

    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:

        '''
        Reaction to the reminder triggered when user is innactive. After showing the articles
        of a topic, will create another reminder, so that a loop is created.
        '''

        read_next_news = tracker.get_slot('read_next_news')

        print("read_next_news: " + str(read_next_news))

        events = []

        article_topic, event = get_next_topic(tracker)
        
        # Display all the articles and get the events of them
        news_events = send_articles(dispatcher, article_topic, True)

        events.append(event)
        events.extend(news_events)

        date = datetime.datetime.now() + datetime.timedelta(seconds =  15)
        entities = tracker.latest_message.get('entities')

        # Create the reminder
        reminder = ReminderScheduled(
            "EXTERNAL_reminder",
            trigger_date_time=date,
            entities=entities,
            name="my_reminder",
            kill_on_user_message=True,
        )

        events.append(reminder)
        return events

       


class ActionGetArticles(Action):

    def name(self) -> Text:
        return "action_show_topic_news"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        '''
        It gets the main headers of the articles
        '''

        try:    
            events = []

            # Get user's input
            input_msg = tracker.get_slot('topic')
            print("Taken entity: " + input_msg)
            
            query_searcher = QuerySearcher()
            article_topic = query_searcher.search_query(input_msg)
            
            events = send_articles(dispatcher, article_topic)

            return events

        except Exception as e:
            print(traceback.format_exc())

            dispatcher.utter_message(response='utter_error_msg')

            events = []
            events.append(SlotSet('topic', ''))
            events.append(SlotSet('global_articles', []))

            return events



class ActionReturnNewsTitle(Action):

    def name(self) -> Text:
        return "action_return_news_title"

    def run(self, dispatcher: CollectingDispatcher, 
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        '''
        Returns the subheader of a chosen article
        '''

        try:

            open_question = tracker.get_slot('open_question')

            # Get user's input
            input_msg = tracker.get_slot('article')
            print("User's input message: " + str(input_msg))
            input_msg = input_msg.replace('"','')
            print("Taken entity of article: " + str(input_msg) )
            
            if open_question:
                global_articles = get_all_articles()

            else:
                # Get all the articles from slot
                global_articles = tracker.get_slot('global_articles')

            query_searcher = QuerySearcher(global_articles.keys())
            input_msg = query_searcher.search_query(input_msg)

            # Get chosen article
            for article in global_articles.keys():
                if article == input_msg:
                    url = global_articles.get(article)
                    last_article = [article, url]
                    break

            # Get the subheader of the article
            subheader = get_sub_header(url)

            buttons = [{"title":"Informazio gehiago eman", "payload":"/more_information"}]
            buttons.append(articles_btn)
            buttons.append(menu_btn)

            dispatcher.utter_message(text=subheader, buttons = buttons, button_type="reply")

            return [SlotSet('last_article', last_article), SlotSet('open_question', False)] 

        except Exception as e:
            dispatcher.utter_message(response = 'utter_error_msg')

            return [SlotSet('last_article', []), SlotSet('open_question', False)]



class ActionGetUrl(Action):

    def name(self) -> Text:
        return "action_return_url"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        '''
        Gets the url of the article depending on the user's choice
        '''

        last_article = tracker.get_slot('last_article')

        try:

            buttons = [articles_btn, menu_btn]
            dispatcher.utter_message(text=last_article[1], buttons = buttons, button_type="reply")

        except Exception as e:
            print(traceback.format_exc())
            dispatcher.utter_message(response='utter_error_msg')

        return []



class ActionShowLastTopicNews(Action):

    def name(self) -> Text:
        return "action_show_last_topic_news"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        '''
        Returns all the articles saved of the last chosen topic
        '''

        global_articles = tracker.get_slot('global_articles')
        
        try:
            article_topic = tracker.get_slot('topic')
            message = "Artikuluen arloa: " + article_topic + "\n \n"
            buttons = []

            # Get all the saved messages
            for article in global_articles.keys():
                message += article + "\n \n"
                entity = article.replace(" artikulua", "")
                buttons.append({"title":article, 
                                "payload":"/choose_news_with_keywords{\"article\":\"" + entity + "\"}"})

            buttons.append(menu_btn)

            dispatcher.utter_message(text=message, buttons=buttons, button_type="reply")

        except Exception as e:
            print(traceback.format_exc())
            dispatcher.utter_message(response="utter_error_msg")

        return []






