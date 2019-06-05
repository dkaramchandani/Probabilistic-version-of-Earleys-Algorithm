#!/usr/bin/env python3


"""
ChartyPy3.py

This is a small incremental bottom-up chart parser for context free grammars.

(C) 2005-2011 by Damir Cavar <damir@cavar.me>

This code is written and distributed under the
Lesser GNU General Public License version 3 or newer.

See http://www.gnu.org/copyleft/lesser.html for details
on the license or the the file lgpl-3.0.txt that should always be
distributed with this code.


Used data structures:

chart:
   list of edges

edge:
   list of integers and symbols
   [start, end, dotindex, LHS, RHS]
   start:    integer, start of the edge
   end:      integer, end of the edge
   dotindex: integer, position of the dot in the RHS
   LHS:      string, left-hand side symbol
   RHS:      list of strings, symbols in right-hand side


Properties:
Incremental (left-to-right) bottom-up chart parser.
Select only potentially appropriate rules from grammar
   - length of RHS is less or equal to remaining words/symbols


Processing steps:
   Word by word:
      Initialise chart with word (add edge for word)
      Do until no further improvement:
         Add new rules from grammar that consume inactive edges
         Apply the fundamental rule to induce new edges


Calling via command line:
If ChartyPy3.py is made executable, one can call it:

./ChartyPy3.py -g PSG1.txt -i "John loves Mary"

or start Python with the script otherwise:

python ChartyPy3.py -g PSG1.txt -i "John loves Mary"

Start the script with as:

python ChartyPy3.py -h

for instructions about the parameters.


This code can be opimized. However, its main purpose is to help students understand a simple algorithm for chart parsing. If there are any bugs, please let me know:

Damir Cavar <damir@cavar.me>
"""

__author__  = "Damir Cavar <damir@cavar.me>"
__date__    = "$May 29, 2005 10:36:30 AM$"
__version__ = "0.5"


import sys, PSGParse3
import argparse
from math import log,exp
DEBUG = False       # set this to 0 if you do not want tracking
QTREE = False


def isActive(edge):
   """Return 1 if edge is active, else return 0."""
   if edge[2] < len(edge[4]): return True
   return False


def isInactive(edge):
   """Return True if edge is active, else returns False."""
   if edge[2] >= len(edge[4]): return True
   return False


def match(aedge, iedge):
   """Returns True if the active edge and the inactive edge match,
      otherwise False.
   """
   if aedge[1] == iedge[0]:
      if aedge[4][aedge[2]] == iedge[3]: return True
   return False


def getParse(inputlength, chart, grammar):
   """TODO: Returns a list of all parses in bracketing notation."""
   parses = []
   for i in range(len(chart)):
      if not isActive(chart[i]):
         if chart[i][0] == 0 and chart[i][1] == inputlength: # got spanning edge
            print("Successfully parsed!")
            #parses.append(struct2Str(chart[i],chart,grammar))
            #print("Chart=",chart)
            #print("edge = ",i)
            #changed to use PROB if we are using parameter -pr, --probability to get probabilistic version of the algorithm
            #also using i instead of chart[i], since i would give location of the edge in the chart which already has the information so no need to save chart[i] structure
            if PROB:
                #adding getProb function call to get probability of the parse as well
                parses.append([struct2Str(i,chart,grammar),getProb(i,chart,grammar)])
            else:
                #only calling the parse since this is without using the probabilistic version
                parses.append(struct2Str(i,chart,grammar))
   return parses


def struct2Str(edge, chart, grammar):
   """TODO: Returns a string representation of the parse with
      labled brackets.

      Parameters:
      edge - the index of edge in the chart
      chart - the current chart (list of edges)
   """
   temporaryString = ""
   #print("Chart:", chart)
   #print("Edge:", edge)
   enums = chart[edge][5]
   temporaryString = "".join((temporaryString, "[", grammar.id2s(chart[edge][3])))
   for symbol in chart[edge][4]:
      if grammar.isTerminal(symbol): #symbols are terminals i.e. they are words of sentence
         temporaryString = " ".join( (temporaryString, grammar.id2s(symbol)) )
      else:                     # symbols are not terminals i.e. not words
         temporaryString = " ".join( (temporaryString, struct2Str(enums[0], chart, grammar)) )
         enums = enums[1:]
      #print("temporaryString:", temporaryString)
   temporaryString = "".join( (temporaryString, " ]") )
   return temporaryString

def getProb(edge, chart, grammar):
    """TODO: Returns a probability of the parse

      Parameters:
      edges - the index of the edge in the chart
      chart - the current chart (list of edges)
    """
    symbollist = []
    total_prob = 0.0
    #total_prob = 1.0
    #print("Chart:", chart)
    #print("Edge:", edge)
    edgenums = chart[edge][5]
    #append to rhs the list of symbols
    symbollist.append(grammar.id2s(chart[edge][3]))
    for x in chart[edge][4]:
      if grammar.isTerminal(x):
         #get terminal so the element preceding this is the lhs of this rule
         rhsterminal = symbollist.pop()
         lhsterminal = grammar.id2s(x)
         #get probability from the myrules dictionary
         prob = float(grammar.myrules[rhsterminal,(lhsterminal,)])
         if prob > 0.0:
            total_prob += log(prob)
            #total_prob *= prob
         #string1 = grammar.myrules[rhsterminal,(lhsterminal,)]
         #print("RHS:{} LHS:{} prob:{} total_prob:{}".format(rhsterminal,lhsterminal,prob,total_prob))
      else:
         #append the remaining elements from the chart's rhs list to our local symbol list
         symbollist.append(grammar.id2s(x))
         #recursive call for the x element
         total_prob += getProb(edgenums[0], chart, grammar)
         #total_prob *= getProb(edgenums[0], chart, grammar)

         #get remaining elements from our chart rhs list
         edgenums = edgenums[1:]
    #all the elements of lhs and rhs are now gathered so the first element in this list is our rhs and remaining are lhs
    #print("Before prob:", total_prob)
    if symbollist: #if any remaining elements are present go inside
        #get probability of the remaining symbols
        prob_int = float(grammar.myrules[symbollist[0],tuple(symbollist[1:])])
        total_prob += log(prob_int)
        #total_prob *= prob_int
        #print("symbollist: {}, After Prob:{}".format(symbollist,total_prob))
    #print("symbollist:", symbollist)
    return total_prob

def edgeStr(edge, grammar):
   """ """
   return str( (edge[0], edge[1], edge[2],
           grammar.id2s(edge[3]),
           grammar.idl2s(edge[4]),
           edge[5]) )


def ruleInvocation(lststart, chart, inputlength, grammar):
   """Add all the rules of the grammar to the chart that
      are relevant:
      Find the rule with the LHS of edge as the leftmost RHS
      symbol and maximally the remaining length of the input.

      Parameters:
      lststart - start position at edge in chart
      chart - the current chart
      inputlength - the length of the input sentence
      grammar - the grammar object raturned by PSGParse3
   """
   change = False
   for i in range(lststart, len(chart)):
      if chart[i][2] >= len(chart[i][4]): # only inactive edge
         (start, end, index, lhs, rhs, consumed) = chart[i]
         for k in grammar.rhshash.get(lhs, ()):
            if len(k[1]) > inputlength - start:
               continue
            newedge = ( start, end, 1, k[0], k[1], (i,) )
            if newedge in chart:
               continue
            chart.append(newedge)
            change = True
            if DEBUG:
               print("RI Adding edge:", edgeStr(newedge, grammar))
   return change


def fundamentalRule(chart, grammar):
   """The fundamental rule of chart parsing generates new edges by
      combining fitting active and inactive edges.

      Parameters:
      chart - the current chart
   """
   change = False
   for aedge in chart:
      if isActive(aedge):
         for k in range(len(chart)):
            if isInactive(chart[k]):
               if match(aedge, chart[k]):
                  newedge = (aedge[0], chart[k][1], aedge[2] + 1,
                             aedge[3], aedge[4], tuple(list(aedge[5]) + [ k ]))
                  if newedge not in chart:
                     chart.append(newedge)
                     change = True
                     if DEBUG:
                        print("FR Adding edge:", edgeStr(newedge, grammar))
   return change


def parse(inp, grammar):
   """Parse a list of tokens.

      Arguments:
      inp = a list of tokens
      grammar = an object returned by PSGParse3
   """
   chart = []
   inputlength = len(inp)

   chartpos = 0  # remember start-position in chart
   for i in range(inputlength):
      # initialize with input token
      rules = grammar.rhshash.get(grammar.symb2id[inp[i]], ( ("", ()) ) )
      for rule in rules:
         if rule[0]:
            chart.append( ( i, i + 1, 1, rule[0], rule[1], () ) )
      if DEBUG:
         print("Adding edge:", edgeStr(chart[len(chart) - 1], grammar))
      change = 1
      while change:
         change = 0
         chartlen = len(chart)
         if ruleInvocation(chartpos, chart, inputlength, grammar):
            change = 1
         chartpos = chartlen  # set pointer to new edge in chart
         if fundamentalRule(chart, grammar):
            change = 1
   if DEBUG:
      print("Chart:")
      for i in range(len(chart)):
         if isActive(chart[i]):
            print(i, "Active:", end=" ")
         else:
            print(i, "Inactive:", end=" ")
         print(edgeStr(chart[i], grammar))
   if QTREE:
      return getQtreeParse(inputlength, chart, grammar)
   return getParse(inputlength, chart, grammar)


def printParses(parses):
   """TODO: Prints the parse as bracketed string to the screen."""

   for j,i in enumerate(parses):
      print("Parsing:", j+1, "of", len(parses))
      #added functionality of PROB to print probability of the parse when using probabilistic version
      if PROB:
          print(i[0])
          #print("With actual probability:", exp(i[1]))
          print("With log probability:", i[1])
      else:
         print(i)

if __name__ == "__main__":
   usage = "usage: %(prog)s [options]"
   parser = argparse.ArgumentParser(prog="ChartyPy", usage=usage,
            description='A chart parser, based on the Earley algorithm.',
            epilog="(C) 2005-2011 by Damir Cavar <damir@cavar.me>")
   parser.add_argument('--version', action='version', version="ChartyPy "+__version__)
   parser.add_argument("-g", "--grammar", dest="grammar", required=True,
            help="name of the file with the context-free grammar")
   parser.add_argument("-i", "--input", dest="sentence", required=True,
            help="input sentence, e.g. \"John kissed Mary\"")
   parser.add_argument("-l", "--latex", dest="latex", action="store_true",
            required=False,
            help="output of parse structure in LaTeX notation for qtree.sty")
   parser.add_argument("-q", "--quiet",
            action="store_false", dest="DEBUG", default=True,
            help="don't print the chart content  [default True]")
   parser.add_argument("-pr", "--prob",
         action="store_true", dest="PROB", default=False,
         help="don't print the probability content  [default False]")

   #parser.add_argument("-p", "--probability", action="store_false",dest="PROB", default= False, help="don't print the log probability of parse  [default False]")
   args = parser.parse_args()
   if args:
      DEBUG = args.DEBUG
      QTREE = args.latex
      PROB  = args.PROB
      #print("VAlue of PROB", PROB)
      try:
         mygrammar = PSGParse3.PSG(args.grammar) # initialization of the grammar
      except IOError:
         print("Cannot load grammar:, args.grammar")
      else:
         printParses(parse(args.sentence.split(), mygrammar))
