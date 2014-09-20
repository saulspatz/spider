# model.py Model for spider solitaire

import random, itertools, pickle
from datetime import date
from collections import namedtuple

ACE = 1
JACK = 11
QUEEN = 12
KING = 13
ALLRANKS = range(1, 14)      # one more than the highest value

# RANKNAMES is a list that maps a rank to a string.  It contains a
# dummy element at index 0 so it can be indexed directly with the card
# value.

SUITNAMES = ('club', 'diamond', 'heart', 'spade')
RANKNAMES = ["", "Ace"] + list(map(str, range(2, 11))) + ["Jack", "Queen", "King"]
COLORNAMES = ("red", "blue")     # back colors

DEAL = (0, 0, 10)     # used in undo/redo stacks

class Stack(list):
  '''
  A pile of cards.
  The base class deals with the essential facilities of a stack, and the derived 
  classes deal with presentation.
  
  The stack knows what cards it contains, but the card does not know which stack it is in.
  
  In reading the code you should realize that > and < for cards indicate successor and
  predecessor, so that Ace of Hearts < Two of Hearts, but no other card.
  '''
  def __init__(self):
    # Bottom card is self[0]; top is self[-1]
    super().__init__()
        
  def add(self, card, faceUp = True):
    self.append(card)
    if faceUp:
      self[-1].showFace()
        
  def isEmpty(self):
    return not self
    
  def clear(self):
    self[:] = []  
      
  def find(self, code):
    '''
    If the card with the given stack is in the stack,
    return its index.  If not, return -1.
    '''
    for idx, card in enumerate(self):
      if card.code == code:
        return idx
    return -1
        
class SelectableStack(Stack):
  '''
  A stack from which cards can be chosen, if they are face up and in sequence,
  from the top of the stack.  When cards are removed, the top card is automatically
  turned up, if it is not laready face up.
  '''
  def __init__(self):
    super().__init__()
    
  def grab(self, n):
    '''
    Remove the card at index k and all those on top of it.
    '''    
    answer = self[k:]
    self = self[:k]
    return answer
        
  def replace(self, cards):
    '''
    Move aborted.  Replace these cards on the stack.
    '''
    self.extend(cards)
    self.moving = None
    
  def canSelect(self, idx):
    if idx >= len(self):
      return False
    if self[idx].faceDown():
      return False
    if not Card.isDescending(self[idx:]):
      return False
    return True
      
class OneWayStack(Stack):
  '''
  Used for the stock and the foundations.
  No cards can be selected.
  Cards are either all face up, or all face down.
  '''
  def __init__(self, faceUp):
    super().__init__()
    self.faceUp = faceUp
    
  def add(self, card):
    super().add(card, self.faceUp)

class Card:
  '''
  A card is identified by its rank, suit, and back color.
  A card knows whether it is face up or own, but does not know 
  which stack it is in.
  '''
  circular = False
  def __init__(self, rank, suit, back):
    self.rank = rank
    self.suit = suit
    self.back = back
    self.up = False   # all cards are initially face down
    self.code = 52*COLORNAMES.index(back)+13*SUITNAMES.index(suit)+rank-1  

  def showFace(self):
    self.up = True
    
  def showBack(self):
    self.up = False
    
  def faceUp(self):
    return self.up
  
  def faceDown(self):
    return not self.faceUp()
  
  # Overloaded operators for predecessor and successor
  
  def __lt__(self, other):
    if self.suit != other.suit:
      return False
    answer = (self.rank == other.rank-1 or 
              (self.circular and self.rank == KING and other.rank == ACE))
    return answer 
  
  def __gt__(self, other):
    return other < self
  
  def __repr__(self):
    return '%s %s %s'%(self.suit, RANKNAMES[self.rank], self.back)
  
  def __str__(self):
    return __repr__(self)
  
  @staticmethod
  def isDescending(seq):
    '''
    Are the cards in a descending sequence of the same suit?
    '''
    return all(map(lambda x, y: x > y, seq, seq[1:]))  

class Model:
  '''
  The cards are all in self.deck, and are copied into the appropriate stacks:
      the stock
      10 waste piles, where all the action is
      8 foundation piles for completed suits
  All entries on the undo and redo stacks are in the form (source, target, n), where
      waste piles are numbered 0 to 9 and foundations 10 to 17, and n is the number
      of cards moved, except that the entry (0, 0, 10) indicates dealing a row of cards,
      and an entry of the form (source, source, 0) indicates turning the top card 
      of the pile face up.
      
    '''
  def __init__(self):
    random.seed()
    self.deck = []
    self.selection = []
    self.undoStack = []
    self.redoStack = []
    self.createCards()
    self.stock = OneWayStack(False)
    self.foundations = []
    for k in range(8):
      self.foundations.append(OneWayStack(True))
    self.waste = []
    for k in range(10):
      self.waste.append(SelectableStack()) 
    self.deal()
    
  def shuffle(self):
    self.stock.clear()
    for f in self.foundations:
      f.clear()
    for w in self.waste:
      w.clear()
    random.shuffle(self.deck)
    for card in self.deck:
      card.showBack()
    self.stock.extend(self.deck)
      
  def createCards(self):
    for rank, suit, back in itertools.product(ALLRANKS, SUITNAMES, COLORNAMES):
      self.deck.append(Card(rank, suit, back))
  
  def deal(self, circular = False, open=False):
    self.circular = Card.circular = circular
    self.open = open
    self.shuffle()
    self.dealDown()
    self.dealUp()
    self.undoStack = []
    self.redoStack = []    
    
  def dealDown(self):
    '''
    Deal the face down cards into the initial layout, unless the
    user has specified open spider.
    '''
    for n in range(44):
      card = self.stock.pop()
      self.waste[n%10].add(card, self.open)
      
  def dealUp(self, redo=False):
    '''
    Deal one row of face up cards
    redo is True if we are redoing a deal
    '''
    for n in range(10):
      card = self.stock.pop()
      self.waste[n].add(card, True)
    if not redo:
      self.undoStack.append(DEAL)
      self.redoStack = []
      
  def canDeal(self):
    '''
    Face up cards can be dealt only if no waste pile is empty
    '''
    return all(self.waste)
         
  def gameWon(self):
    '''
    The game is won when all foundation piles are used
    '''
    return min([len(f) for f in self.foundations]) == 13
  
  def downUp(self, k):
    '''
    Return a tuple (down, up) with the number of face down
    cards and the number of face up cards in waste[k]
    '''
    w = self.waste[k]
    down = len([card for card in w if card.faceDown()])
    return (down, len(w) - down)
  
  def grab(self, k, idx):
    '''
    Initiate a move between waste 
    Grab card idx and those on top of it from waste pile k
    Return a code numbers of the selected cards.
    We need to remember the data, since the move may fail.
    '''
    w = self.waste[k]
    if not w.canSelect(idx):
      return []
    self.moveOrigin = k
    self.moveIndex = idx
    self.selection = w[idx:]
    return self.selection
  
  def abortMove(self):
    self.selection = []
    
  def moving(self):
    return self.selection != [] 
  
  def getSelected(self):
    return self.selection
  
  def canDrop(self, k):
    '''
    Can the moving cards be dropped on waste pile k?
    '''
    dest = self.waste[k]
    source = self.selection
    
    if not self.selection:
      return False
    if not dest:      # can always drop on empty pile
      return True
    if dest[-1].rank - source[0].rank == 1:  
      return True       # e.g. can drop a 4 on a 5
    if self.circular:   # can place King on ACE
      return dest[-1].rank == ACE and source[0].rank == KING
  
  def completeMove(self, dest):
    '''
    Compete a legal move.
    Tranfer the moving cards to the destination stack.
    Turn the top card of the source stack face up, if need be.
    '''
    source = self.waste[self.moveOrigin]
    moving = self.selection
    target = self.waste[dest] if dest < 10 else self.foundations[dest-10]
    target.extend(self.selection)
    #while len(source) > self.moveIndex:
      #source.pop()
    source[:] = source[:self.moveIndex]
    self.undoStack.append((self.moveOrigin, dest, len(self.selection)))
    self.flipTop(self.moveOrigin)
    self.selection = []
    self.redoStack = []
    
  def selectionToFoundation(self, dest):
    '''
    Complete a legal move to foundation pile
    '''
    self.completeMove(dest+10)
    
  def selectionToWaste(self, dest):
    '''
    Complete a legal move to waste pile
    '''
    self.completeMove(dest)  
        
  def completeSuit(self, pile, idx):
    '''
    *** Performs an action, and returns True (success) or False (failure).  ***
    If pile contains a comple suit, and index indicates one of the 
    top 13 cards, move the suit to the first available foundation,
    and return True.  Otherwise, return False.
    '''
    w = self.waste[pile]
    if len(w) < 13 or idx < len(w) - 13:
      return False
    
    if w[-13].faceDown() :
      return False
    if not Card.isDescending(w[-13:]):
        return False
      
    for i, f in enumerate(self.foundations):
      if f.isEmpty(): break
    for  card in w[-13:]:
      f.add(card)
    #for k in range(13):
      #w.pop()
    w[:] = w[:-13]
    self.flipTop(pile)
    self.undoStack.append((pile, i+10, 13))
    self.redoStack = []
    return True
  
  def flipTop(self, k):
    '''
    Turn the top card of waste pile k face up, if need be
    '''
    w = self.waste[k]
    try:
      if w[-1].faceDown():
        w[-1].showFace()
        self.undoStack.append((k,k,0))
    except IndexError:
      pass
  
  def movingCompleteSuit(self):
      return len(self.selection) == 13
    
  def win(self):
    return all((len(f) for f in self.foundations)) 
  
  def undo(self):
    ''''
    Pop a record off the undo stack and undo the corresponding move.
    If the move is a flipTop, undo the next move also.
    '''
    (s, t, n) = self.undoStack.pop()
    if (s, t, n) == DEAL:
      self.undeal()
    elif s == t:      # flipTop called
      self.waste[s][-1].showBack()
      self.redoStack.append((s,t,n))
      self.undo()
    else:
      source = self.waste[s] if s < 10 else self.foundations[s-10]
      target = self.waste[t] if t < 10 else self.foundations[t-10]
      assert len(target) >= n
      source.extend(target[-n:])
      #for k in range(n):
        #target.pop()
      target[:] = target[:-n]
      self.redoStack.append((s,t,n))
  
  def undeal(self):
    '''
    Undo a deal of a row of cards
    '''
    for w in reversed(self.waste):
      assert w
      card = w.pop()
      card.showBack()
      self.stock.append(card)
    self.redoStack.append(DEAL)

  def redo(self):
    ''''
    Pop a record off the redo stack and redo the corresponding move.
    If the next move is a flipTop, redo the next move also.
    ''' 
    (s, t, n) = self.redoStack.pop()
    if (s, t, n) == DEAL:
      self.dealUp(True) 
    else:
      source = self.waste[s] if s < 10 else self.foundations[s-10]
      target = self.waste[t] if t < 10 else self.foundations[t-10]
      assert n <= len(source)
      target.extend(source[-n:])
      #for k in range(n):
        #source.pop()
      source[:] = source[:-n]  
    self.undoStack.append((s,t,n))
    
    try:
      (s, t, n) = self.redoStack[-1]
      if  s == t and n == 0:    # flip top
        self.redoStack.pop()
        self.waste[s][-1].showFace()
        self.undoStack.append((s, t, n))
    except IndexError:
      pass
      
  def canUndo(self):
    return self.undoStack != []
  
  def canRedo(self):
      return self.redoStack != []  
    
  def save(self, filename):
    with open(filename, 'wb') as fn:
      pickle.dump((self.deck, self.undoStack, self.redoStack, self.stock, self.foundations, self.waste, self.circular, self.open), fn)
      
  def load(self, filename):
    '''
    Read a saved game from filename, reconstitute the game, and display it.
    '''
    with open(filename, 'rb') as fin:
      self.deck, self.undoStack, self.redoStack, self.stock, self.foundations, self.waste, self.circular, self.open = pickle.load(fin) 
      
  def dealsLeft(self):
    return len(self.stock) // 10
  
  def moves(self):
    return len([m for m in self.undoStack if m[0] != m[1]])
  
  Stats = namedtuple('Stats', ['variant', 'win', 'moves', 'up', 'up1', 'date'])
  SummaryStats = namedtuple('SummaryStats', ['variant', 'games', 'win', 'moves', 'up', 'up1'])

  def stats(self):
    # variant is 'Standard,' 'Circular', 'Open', or 'Both'
    # win is boolean
    # Moves is number of moves made
    # up is total face down cards turned up
    # upFirst is cards turned up on first deal
    
    date = date.today().strftime('%x')
    circ = self.circular
    op = self.open
    if not circ:
      variant = 'Standard' if not op else 'Open'
    else:
      variant = 'Circular' if not op else 'Both'
    win = self.win()
    moves = self.moves()
    spec = [m for m in self.undoStack if m[0] == m[1]]
    up = len([m for m in spec if m[2] == 0] )
    upFirst = len(tuple(takewhile(lambda m: m[2] == 0, spec)))
    return Stats(variant, win, moves, up, upFirst, date)
  
      
    
  
    