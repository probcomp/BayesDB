#
#   Copyright (c) 2010-2014, MIT Probabilistic Computing Project
#
#   Lead Developers: Jay Baxter and Dan Lovell
#   Authors: Jay Baxter, Dan Lovell, Baxter Eaves, Vikash Mansinghka
#   Research Leads: Vikash Mansinghka, Patrick Shafto
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#

from pyparsing import Literal, CaselessLiteral, Word, Upcase, delimitedList, Optional,\
    Combine, Group, alphas, nums, alphanums, ParseException, Forward, oneOf, quotedString,\
    ZeroOrMore, OneOrMore, restOfLine, Keyword

selectStatement = Forward()

identifier = Word(alphas, alphanums + "_")


selectToken = Keyword("select", caseless=True)
fromToken = Keyword("from", caseless=True)
orderByToken = Keyword("order", caseless=True) + Keyword("by", caseless=True)
limitToken = Keyword("limit", caseless=True)

columnNameList = Group(delimitedList(identifier | '*'))

createBtableStatement = Keyword("create", caseless=True) + Keyword("btable", caseless=True) + \
                        identifier.setResultsName("tablename") + fromToken + identifier.setResultsName("filename")

#orderByClause = orderByToken + 

selectStatement << ( selectToken +
                     columnNameList.setResultsName("columns") +
                     fromToken +
                     identifier.setResultsName("tablename") +
                     Optional(whereClause) +
                     Optional(orderByClause) +
                     Optional(limitClause) )

BQLStatement = (selectStatement | createBtableStatement) + Optional(';')

BQL = ZeroOrMore(BQLStatement)

## allows comments
dashComment = "--" + restOfLine
BQL.ignore(dashComment)



def test( str ):
    print str,"->"
    try:
        tokens = BQL.parseString( str )
        print "tokens = ",        tokens
        print "tokens.tablename =", tokens.tablename
        print "tokens.filename =",  tokens.filename
        #print "tokens.where =", tokens.where
    except ParseException, err:
        print " "*err.loc + "^\n" + err.msg
        print err
    print


class PyParser(object):
    def __init__(self):
        pass

    def parse(self, bql_string):
        pass

    def parse_line(self, bql_string):
        pass
