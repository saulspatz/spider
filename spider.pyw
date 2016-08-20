#!/usr/local/bin/python3
# spider.pyw

'''
Spider solitaire.  I wrote this because the games I find online have various deficiencies. 
Most annoyingly, they dn't leave enough vertical space between the cards so that you
can see the suits.  In most cases, all you can tell is the rank and color.
Also, they use the protocol that when the player completes a suits from King to Ace, it is 
automatically taken out of play immediately. The rule is that it remains in play until
the player takes it out.  Often, this can be used to great advantage in organizing other piles.
'''
from model import Model 
from view import View
import tkinter as tk
from tkinter.messagebox import showerror, showinfo, askokcancel
from datetime import datetime
import sys, os
from utils import ScrolledList

FMT  = '%Y_%m_%d_%H_%M_%S'      # format strings for datetime objects
FMT2 = '%x %X'

helpText = '''
OBJECTIVE
Spider is played with two decks of 52 cards each.  The objective is to arrange each of the eight suits in sequence from the King down to the Ace.  When a suit is arranged in sequence, it may be removed to a foundation pile.  If all suits are moved to the foundations, the game is won.

SETUP
There are ten waste piles.  The leftmost four initially have six cards each, and the remaining six initially have five cards each.  The remaining 50 cards are placed in the stock.  There are also eight foundation piles.  All the interesting action takes place in the waste piles. 

MOVING CARDS
Any card may be place on top of another card that is one higher in rank.  For example, a 7 may be moved on top of an 8, or a Queen on top of a King; suits and colors don't matter for this purpose.  A run of cards in the same suit in descending sequence is available for play, but you don't have to move all of them.  For example, if the top three cards of some pile are the 3, 4, and 5 of Spades, you can move the 3 on top of a 4, the 3 and 4 on top of a 5, or all three on top of a 6. 

If you have an empty waste pile, you can move any cards available for play onto the empty pile.  

If a move leaves a face-down card showing on the top of a pile, that card is turned face up.

COMPLETE SUITS
Once you have arranged a comple suit in order from the King down to the Ace, you can remove it to a foundation pile, but you needn't do so immediately.  You can use it to help organize the other cards in the waste piles.  This is often very useful.

DEALING
When there are no more moves you care to make, you can deal another row.  You deal by clicking the stock.  This deals one card face up on each of the waste piles.  You may not deal if there is an empty waste pile.

STRATEGY
Turn as many cards as possible face up.  It is unusual to turn all cards face up and lose.  

Make plays that form runs of the same suit before plays that do not.  Given a choice of two places to play a card, you should naturally play it on a card of the same suit, if possible.

Make plays that involve a choice before plays that do not.  If you place the 7 of Clubs on the 8 of Hearts instead of the 8 of Spades, and then the 9 of Hearts turns up, you can move the 7 to the 8 of Spades and then play 8 of Hearts to the 9.

Make plays involving higher cards earlier.   If you have a 2, 3, 5, and 6 available for play, move the 5 on top of the 6.  If a 4 shows up, you'll be able to move the 3 and 2 also.

The most important thing in organizing the waste piles are empty piles, or "spaces".  These can be used to organize the other waste piles.  One space is good, two are better, and three are very powerful.  Don't fill in a space with a permanent card until you have exploited it to the utomost.

VARIANTS 
In circular spider solitaire, a King may be placed on top of an Ace and a run may have a King on top of an Ace, so that the 3, 2, Ace, King, Queen of Clubs can be moved onto a 4.  A run can comprise more than 13 cards.  The run must still be in sequence from King down to Ace before being moved to a foundation pile.

'''        
class Spider:
  def __init__(self):
    self.model = Model()
    self.view = View(self, self.quit, width=1000, height=1000, scrollregion=(0, 0, 950, 3000) )
    self.makeHelp()
    self.circular = tk.BooleanVar()
    self.open = tk.BooleanVar() 
    self.circular.set(False)
    self.open.set(False)
    self.circular.trace('w', self.optionChanged)
    self.open.trace('w', self.optionChanged)
    self.makeMenu()
    self.view.start()      #  start the event loop
        
  def deal(self):
    model = self.model
    model.deal(self.circular.get(), self.open.get())
    self.view.show()
    
  def makeHelp(self):
    top = self.helpText = tk.Toplevel()
    top.transient(self.view.root)
    top.protocol("WM_DELETE_WINDOW", top.withdraw)
    top.withdraw()
    top.resizable(False, True)
    top.title("Spider Help")
    f = tk.Frame(top)
    self.helpText.text = text = tk.Text(f, height=30, width=80, wrap=tk.WORD)
    text['font'] = ('helevetica', 12, 'normal')
    text['bg'] = '#ffef85'
    text['fg'] = '#8e773f'
    scrollY = tk.Scrollbar(f, orient=tk.VERTICAL, command=text.yview)
    text['yscrollcommand'] = scrollY.set
    text.grid(row=0, column=0, sticky='NS')
    f.rowconfigure(0, weight=1)
    scrollY.grid(row=0, column=1, sticky='NS')
    tk.Button(f, text='Dismiss', command=top.withdraw).grid(row=1, column=0)
    f.grid(sticky='NS')
    top.rowconfigure(0, weight=1)
    text.insert(tk.INSERT,helpText)
    
  def makeMenu(self):
    top = self.view.menu
    
    game = tk.Menu(top, tearoff=False)
    game.add_command(label='New', command=self.deal)
    game.add_command(label='Quit', command=self.quit)
    top.add_cascade(label='Game', menu=game)
       
    options = tk.Menu(top, tearoff=False)
    options.add_checkbutton(label='Circular', variable=self.circular)
    options.add_checkbutton(label='Open',  variable=self.open)
    top.add_cascade(label='Options', menu=options)
       
    top.add_command(label='Help', command = self.showHelp)  
     
  def notdone(self):
    showerror('Not implemented', 'Not yet available') 

  def showHelp(self):
    self.helpText.deiconify()
    self.helpText.text.see('1.0')  
  
  def optionChanged(self, *args):
    self.model.reset(self.circular.get(), self.open.get())
    self.model.adjustOpen(self.open.get())
    self.view.show()
  
  def quit(self):
    self.view.root.quit()
      
if __name__ == "__main__":
  Spider()
    