__author__ = 'omarsar'

#A set of NLP-based function to extract concepts from short or long text.

import requests
import json
import psycopg2
import urllib
import sys
import os
import re
import codecs
import json
from collections import defaultdict
import csv
from twython import Twython
import time
import pymongo
from pymongo import MongoClient
import csv
import datetime
from time import gmtime, strftime
from time import strptime
from time import mktime
from datetime import datetime
from nltk.tokenize import WhitespaceTokenizer
import nltk
from nltk.corpus import stopwords
from nltk.util import ngrams


#Check if an item is adjective
def checkIfAdjective(word):

	tokens  = WhitespaceTokenizer().tokenize(word)
	tagged = nltk.pos_tag(tokens)
	namedEnt = nltk.ne_chunk(tagged, binary=True)

	for t in tagged:
		if t[1]=='JJ' or t[1] == 'JJR' or t[1] == 'JJS': 
			return True
		else:
			return False

#Check if a term is an integer
def checkIfInteger(word):

	tokens  = WhitespaceTokenizer().tokenize(word)
	tagged = nltk.pos_tag(tokens)
	namedEnt = nltk.ne_chunk(tagged, binary=True)

	for t in tagged:
		if t[1]=='CD': 
			return True
		else:
			return False

#check if a term is a noun
def checkIfNoun(word):

	tokens  = WhitespaceTokenizer().tokenize(word)
	tagged = nltk.pos_tag(tokens)
	namedEnt = nltk.ne_chunk(tagged, binary=True)

	for t in tagged:
		if t[1]=='NN' or t[1]=='NNS' or t[1]=='NNP' or t[1]=='NNPS': 
			return True
		else:
			return False

#Return the actual part of speech of a tweet in form of an array
def getActualPOS(word):
	wordstoreturn = []
	tokens  = WhitespaceTokenizer().tokenize(word)
	tagged = nltk.pos_tag(tokens)
	namedEnt = nltk.ne_chunk(tagged, binary=True)

	for t in tagged:
		#if t[1]=='NN' or t[1]=='NNS' or t[1]=='NNP' or t[1]=='NNPS': #This is only used for the word cloud ->: or t[1]=='JJ' or t[1]=='VB' or t[1]=='VBD' or t[1]=='VBG' or t[1]=='VBN' or t[1]=='VBP' or t[1]=='VB':
		wordstoreturn.append(t[1])

	return wordstoreturn

#Return the items that are nouns
def getPOS(word):
	wordstoreturn = []
	tokens  = WhitespaceTokenizer().tokenize(word)
	tagged = nltk.pos_tag(tokens)
	namedEnt = nltk.ne_chunk(tagged, binary=True)

	for t in tagged:
		if t[1]=='NN' or t[1]=='NNS' or t[1]=='NNP' or t[1]=='NNPS': #This is only used for the word cloud ->: or t[1]=='JJ' or t[1]=='VB' or t[1]=='VBD' or t[1]=='VBG' or t[1]=='VBN' or t[1]=='VBP' or t[1]=='VB':
			wordstoreturn.append(t[0])

	return wordstoreturn

#Gets Bigrams (set of two words)
def getBigrams(tweet):
	joinedtweet = tweet #' '.join(tweet)
	tosendtweet = []
	for item in nltk.bigrams (joinedtweet.split()): tosendtweet.append(' '.join(item))
	return tosendtweet

#Gets Trigrams (set of three words)
def getTrigrams(tweet):
	joinedtweet = tweet
	tosendtweet = []
	for item in nltk.trigrams(joinedtweet.split()): tosendtweet.append(' '.join(item))
	return tosendtweet

#get individual words
def getUnigram(tweet):
	tosendtweet = []
	for item in tweet.split(): tosendtweet.append(item)

	return tosendtweet

#get n-grams (set of n-words, specify your n)
def getNGrams(n, tweet):
	tosendtweet = []	
	for item in ngrams(tweet.split(), n): tosendtweet.append(' '.join(item))

	return tosendtweet

#check if the first term is Capitalized
def checkIfCapitalized(word):
	if word[0].isupper():
		return True
	else:
		return False

#Function to help remove stopwords from a piece of text
def removeStopWords(tweet):
	final = ' '.join([word for word in tweet.split() if word not in cachedStopWords] )
	return final

#Rule 1: Check for unigrams Nouns and if the first letter is capitalized (e.g. Basketball)
def Rule_1(t):
	rule1Array = []
	for word in getPOS(t):
		if checkIfCapitalized(word) == True:
			rule1Array.append(word)

	return rule1Array

#Rule 2: Check for compound nouns (e.g. Christmas Eve)
def Rule_2(t):
	rule2Array = []
	#first check for Bigrams...
	for sequence in getBigrams(t):
		sequenceToArray = []
		for w in sequence.split(): sequenceToArray.append(w) 
		if checkIfCapitalized(sequenceToArray[0]) == True and checkIfNoun(sequenceToArray[0]) == True\
		and checkIfCapitalized(sequenceToArray[1]) == True and checkIfNoun(sequenceToArray[1]) == True:
			rule2Array.append(sequence) 

	#... and then Trigrams #TODO: I can improve if it identifies the Trigrams then exclude doing Bigrams for consistency
	for sequence in getTrigrams(t):
		sequenceToArray = []
		for w in sequence.split(): sequenceToArray.append(w)
		if checkIfCapitalized(sequenceToArray[0]) == True and checkIfNoun(sequenceToArray[0]) == True\
		and checkIfCapitalized(sequenceToArray[1]) == True and checkIfNoun(sequenceToArray[1]) == True \
		and checkIfCapitalized(sequenceToArray[2]) == True and checkIfNoun(sequenceToArray[2]) == True:
			rule2Array.append(sequence) 

	return rule2Array

#Rule 3: A word sequence "cover of a Harry Patter"
def Rule_3(t):
	rule3Array = []
	#first check for 3 words
	for sequence in getNGrams(3,t):
		sequenceToArray = []
		for w in sequence.split(): sequenceToArray.append(w)
		if sequenceToArray[1] == "of" and checkIfCapitalized(sequenceToArray[2]) == True \
		and checkIfNoun(sequenceToArray[0]) == True and checkIfNoun(sequenceToArray[2]) == True:
			rule3Array.append(sequence) 

	#then check for 4 words
	for sequence in getNGrams(4,t):
		sequenceToArray = []
		for w in sequence.split(): sequenceToArray.append(w)		
		if sequenceToArray[1] == "of" and checkIfCapitalized(sequenceToArray[2]) == True\
		and checkIfCapitalized(sequenceToArray[3]) == True and checkIfNoun(sequenceToArray[2]) == True\
		and checkIfNoun(sequenceToArray[3]) == True and checkIfNoun(sequenceToArray[0]) == True:
			rule3Array.append(sequence) 

	return rule3Array

# Rule 4: "Toyota 86" is a sequence with a noun and a numeric and it checks in reverse order as well (e.g. 311 earthquake)
def Rule_4(t):
	rule4Array = []

	#first check if nnoun -> integer
	for sequence in getBigrams(t):
		sequenceToArray = []
		for w in sequence.split(): sequenceToArray.append(w)
		if checkIfCapitalized(sequenceToArray[0]) == True and checkIfNoun(sequenceToArray[0]) == True\
		and checkIfInteger(sequenceToArray[1]) == True:
			rule4Array.append(sequence)  

	#then check if integer -> noun
	for sequence in getBigrams(t):
		sequenceToArray = []
		for w in sequence.split(): sequenceToArray.append(w)
		if checkIfInteger(sequenceToArray[0]) == True and checkIfNoun(sequenceToArray[1]) == True:
			rule4Array.append(sequence)

	return rule4Array

#rule 5: is a sequence with adjective and noun (e.g. desperate housewives)
def Rule_5(t):
	rule5Array = []
	iterator = 0
	numOfWords = len(t.split())
	tweetArray = [] 
	
	tweetPOSArray = getActualPOS(t)
	for item in t.split(): tweetArray.append(item)

	for n in range(numOfWords-1):
		#sliding window on tweet needed here since we need to consider the entire text rather than individual words or bigrams
		if (tweetPOSArray[n] == 'JJ' or tweetPOSArray[n] == 'JJR' or tweetPOSArray[n] == 'JJS')  and \
		(tweetPOSArray[n+1] == 'NNP' or tweetPOSArray[n+1] == 'NNPS' or \
			tweetPOSArray[n+1]=='NN' or tweetPOSArray[n+1] == 'NN'):
			rule5Array.append(tweetArray[n]+" "+tweetArray[n+1]) 

	return rule5Array		

			
#MAIN##########################################################
#load the Stopwords
#cachedStopWords = stopwords.words("english")

print (Rule_1("Hey I want to go to Seattle really bad"))
#Rule_2("Can't wait for Christmas Day Eve to arrive")
#Rule_3("I really like the cover of GQ Magazine")
#Rule_4("Testing this 86 toyota")
#Rule_5("There is a desperate mouse in my house")
#print (getNGrams(4,"Can't wait for Christmas Day Eve to arrive"))
#print (getPOS('Christmas Eve'))
#print(removeStopWords("Hey I want to go to Seattle really bad"))

