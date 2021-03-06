# view.py
'''
The visual interface for spider solitaire.
The view knows about the model, but not vice versa
Thce canvas widget is used for both view and controller.
'''
import sys, os, itertools
import tkinter as tk
from model import SUITNAMES, RANKNAMES, ALLRANKS, Card
from tkinter.messagebox import showerror
from utils import ScrolledCanvas
from tkinter.simpledialog import SimpleDialog

# Constants determining the size and layout of cards and stacks.  We
# work in a grid where each stack is surrounded by MARGIN
# pixels of space on each side, so adjacent stacks are separated by
# 2*MARGIN pixels.  OFFSET1 is the offset used for displaying the
# a card above a face down card, and OFFSET2 is the offset used
# for displaying a card above a face up card.

CARDWIDTH = 75
CARDHEIGHT = 113
MARGIN = 10
XSPACING = CARDWIDTH + 2*MARGIN
YSPACING = CARDHEIGHT + 4*MARGIN
OFFSET1 = 8
OFFSET2 = 20

BACKGROUND = '#070'
OUTLINE = '#060'        # outline color of foundation files
CELEBRATE = 'yellow'     # Color of "you won" message
BUTTON = 'forest green'

# Cursors
DEFAULT_CURSOR = 'arrow'
SELECT_CURSOR = 'hand2'

STATUS_FONT = ('Helvetica', '12', 'normal')
STATUS_BG = 'gray'

SCROLL_INTERVAL = 5     # miliseconds
SCROLL_DISTANCE = '2m'
imageDict = {}   # hang on to images, or they may disappear!

class ButtonBar(tk.Canvas):
  def __init__(self, parent):
    super().__init__(parent, bg=BACKGROUND, bd=0, highlightthickness=0)
    self.configure(height=5*MARGIN,width=10*XSPACING)
    width=int(self['width'])
    self.makeButton(width//2-12*MARGIN, 'undo')
    self.makeButton(width//2-4*MARGIN, 'redo')
    self.makeButton(width//2+4*MARGIN, 'restart')
    self.makeButton(width//2+12*MARGIN, 'redeal')
    self.place(in_=parent, relx=.5,y=0,anchor=tk.N)    
  
  def makeButton(self, left, text):
    self.create_oval(left, MARGIN, left+6*MARGIN, 4*MARGIN, fill=BUTTON, outline=BUTTON, tag = text)
    self.create_text(left+3*MARGIN,2.5*MARGIN,text=text.title(),fill=CELEBRATE,tag=text,anchor=tk.CENTER)
 
class View: 
  '''
  Cards are represented as canvas image iitems,  displaying either the face
  or the back as appropriate.  Each card has the tag "card".  This is 
  crucial, since only canvas items tagged "card" will respond to mouse
  clicks.
  '''
  def __init__(self, parent, quit, **kwargs):
    # kwargs passed to Scrolled Canvas
    # quit is function to call when main window is closed
    self.parent = parent          # parent is the Spider application
    self.model =  parent.model
    self.root = root = tk.Tk()
    root.protocol('WM_DELETE_WINDOW', quit)
    width = 4*MARGIN+10*XSPACING
    self.root.wm_geometry('%dx850-10+10'%width)
    root.title("Spider Solitaire")

    root.minsize(width=width, height=500)
    root.maxsize(width=width, height=2500)
    self.menu = tk.Menu(root)         # parent constructs actual menu         
    root.config(menu=self.menu)                 
    self.waste = []           # NW corners of the waste piles
    self.foundations = []   # NW corners of the foundation piles
    x = 2*MARGIN
    y = 5* MARGIN
    self.stock = (x,y)      #NW corner of stock
    x += XSPACING
    for k in range(8):
      x += XSPACING
      self.foundations.append((x, y))
    y += YSPACING
    x = 2*MARGIN
    for k in range(10):
      self.waste.append((x, y)) 
      x += XSPACING 

    status = tk.Frame(root, bg = STATUS_BG)
    self.circular = tk.Label(status, text = " Circular ", relief = tk.RIDGE, font = STATUS_FONT,
                             bg = STATUS_BG, fg = 'Black', bd = 2)
    self.open =     tk.Label(status, text = " Open     ", relief = tk.RIDGE, font = STATUS_FONT, 
                             bg = STATUS_BG, fg = 'Black', bd = 2)
    self.deals =    tk.Label(status, relief = tk.RIDGE, font = STATUS_FONT, 
                             bg = STATUS_BG, fg = 'Black', bd = 2)
    self.down =    tk.Label(status, relief = tk.RIDGE, font = STATUS_FONT, 
                            bg = STATUS_BG, fg = 'Black', bd = 2)
    self.moves =    tk.Label(status, relief = tk.RIDGE, font = STATUS_FONT, 
                             bg = STATUS_BG, fg = 'Black', bd = 2)
    self.circular.pack(expand=tk.NO, fill = tk.NONE, side = tk.LEFT)
    self.open.pack(expand=tk.NO, fill = tk.NONE, side = tk.LEFT)
    self.deals.pack(expand=tk.NO, fill = tk.NONE, side = tk.RIGHT)
    self.down.pack(expand=tk.NO, fill = tk.NONE, side = tk.RIGHT)
    self.moves.pack(expand=tk.NO, fill = tk.NONE, side = tk.RIGHT)
    tableau = self.tableau = ScrolledCanvas(root, bg=BACKGROUND, cursor=DEFAULT_CURSOR, 
                                            scrolls=tk.VERTICAL, bd=0, highlightthickness=0, **kwargs)
    self.tableau.canvas['yscrollincrement'] = SCROLL_DISTANCE
    status.pack(expand=tk.NO, fill = tk.X, side=tk.BOTTOM)
    tableau.pack(expand=tk.YES, fill=tk.Y)
    width = kwargs['width']
    height = kwargs['height']
    
    self.loadImages()
    self.createCards()
    tableau.tag_bind("card", '<ButtonPress-1>', self.onClick)
    tableau.tag_bind("card", '<Double-Button-1>', self.onDoubleClick)
    tableau.canvas.bind('<B1-Motion>', self.drag)
    tableau.canvas.bind('<ButtonRelease-1>', self.onDrop)
    
    
    # Avoid scroll wheel problems on some Mac installations
    if sys.platform != 'darwin':
      tableau.canvas.bind('<Button-4>', self.scrollWheel)
      tableau.canvas.bind('<Button-5>', self.scrollWheel)
      tableau.canvas.bind('<MouseWheel>', self.scrollWheel)
      
    for w in self.waste:
          tableau.create_rectangle(w[0], w[1], w[0]+CARDWIDTH, w[1]+CARDHEIGHT, outline = OUTLINE)    
    for f in self.foundations:
      tableau.create_rectangle(f[0], f[1], f[0]+CARDWIDTH, f[1]+CARDHEIGHT, outline = OUTLINE)
    tableau.create_text(self.foundations[0][0], self.foundations[0][1]+CARDHEIGHT, 
                        text = "'The game is done! I've won! I've won!'\nQuoth she, and whistles thrice.",
                        fill = BACKGROUND, font=("Times", "32", "bold"), tag = 'winText', anchor=tk.NW)
    self.scrolling = False
    self.buttons = ButtonBar(self.tableau)
    self.buttons.tag_bind('undo', '<ButtonPress-1>', self.undo)
    self.buttons.tag_bind('redo', '<ButtonPress-1>', self.redo)
    self.buttons.tag_bind('restart', '<ButtonPress-1>', self.restart)
    self.buttons.tag_bind('redeal', '<ButtonPress-1>', self.redeal)    
    self.show()
    
  def start(self):
    self.root.mainloop()
      
  def loadImages(self):
    PhotoImage = tk.PhotoImage
    cardDir = os.path.join(os.path.dirname(sys.argv[0]), 'cards') 
    blue = PhotoImage(file=os.path.join(cardDir,'blueBack.gif'))
    red = PhotoImage(file=os.path.join(cardDir,'redBack.gif'))
    imageDict['blue'] = blue
    imageDict['red'] = red    
    for rank, suit in itertools.product(ALLRANKS, SUITNAMES):
      face = PhotoImage(file = os.path.join(cardDir, suit+RANKNAMES[rank]+'.gif'))               
      imageDict[rank, suit] = face
      
  def createCards(self):
    model = self.model
    canvas = self.tableau    
    for card in model.deck:
      c = canvas.create_image(-200, -200, image = None, anchor = tk.NW, tag = "card")
      canvas.addtag_withtag('code%d'%card.code, c)
      
  def showWaste(self, k):
    '''
    Display waste pile number k
    '''
    x, y = self.waste[k]
    canvas = self.tableau
    for card in self.model.waste[k]:
      tag = 'code%d'%card.code
      canvas.coords(tag, x, y)
      if card.faceUp():
        foto = imageDict[card.rank, card.suit]
        y += OFFSET2
      else:
        foto = imageDict[card.back]
        y += OFFSET1
      canvas.itemconfigure(tag, image = foto)
      canvas.tag_raise(tag) 

  def show(self):
    model = self.model
    canvas = self.tableau
    self.showStock()
    for k in range(10):
      self.showWaste(k)
    for k in range(8):
      self.showFoundation(k)
    if model.canUndo():
      self.enableUndo()
    else:
      self.disableUndo()
    if model.canRedo():
      self.enableRedo()
    else:
      self.disableRedo() 
    color = 'Black' if model.circular else STATUS_BG
    self.circular.configure(fg=color)
    color = 'Black' if model.open else STATUS_BG
    self.open.configure(fg=color)    
    color = CELEBRATE if model.win() else BACKGROUND
    canvas.itemconfigure('winText', fill=color)
    self.deals.configure(text='Deals %d'%model.dealsLeft())
    self.down.configure(text='Down %d'%model.downCards())
    self.moves.configure(text='Moves %d'%model.moves())
    if model.win():
      self.tableau.canvas.yview_moveto(0.0)
    
  def dealUp(self):
    self.model.dealUp()
    self.show()
      
  def showFoundation(self, k):
    model = self.model
    canvas = self.tableau
    x, y = self.foundations[k]
    for card in model.foundations[k]:
      tag = 'code%d'%card.code
      canvas.itemconfigure(tag, image = imageDict[card.rank, card.suit])
      canvas.coords(tag,x,y)
      canvas.tag_raise(tag)
      
  def showStock(self):
    model = self.model
    canvas = self.tableau
    x, y = self.stock
    for card in model.stock:
      tag = 'code%d'%card.code
      canvas.itemconfigure(tag, image = imageDict[card.back])
      canvas.coords(tag,x,y)
      canvas.tag_raise(tag)    
                   
  def grab(self, selection, k, mouseX, mouseY):
    '''
    Grab the cards in selection.
    k is the index of the source waste pile.
    Note that all the cards are face up.
    '''
    canvas = self.tableau
    if not selection:
      return
    self.mouseX, self.mouseY = mouseX, mouseY
    self.yfraction = canvas.canvas.yview()[0]
    west = self.waste[k][0]
    for card in selection:
      tag = 'code%s'%card.code
      canvas.tag_raise(tag)
      canvas.addtag_withtag("floating", tag)
    canvas.configure(cursor=SELECT_CURSOR)
    dx = 5 if mouseX - west > 10 else -5
    canvas.move('floating', dx, 0)
    
  def drag(self, event):
    canvas = self.tableau.canvas
    sd = self.scrollDirection()
    if not self.scrolling and sd != 0:
      self.scrolling = True
      canvas.after(SCROLL_INTERVAL, self.autoScroll, sd)
    elif self.scrolling and sd == 0:
      self.scrolling = False
    try:
      x, y = event.x, event.y
      dx, dy = x - self.mouseX, y - self.mouseY
      self.mouseX, self.mouseY = x, y
      canvas.move('floating', dx, dy)
    except AttributeError:
      pass
    
  def scrollDirection(self):
    '''
    Return values:
      1: scroll down
      -1: scroll up
      0: don't scroll
    SIDE EFFECT:
      Set SCROLL_INTERVAL to value dependent on how far the card's been dragged
    '''
    global SCROLL_INTERVAL
    si = (50, 40, 30, 20, 10, 5)
    answer = 0
    canvas = self.tableau.canvas
    north, south = canvas.yview()
    extent = int(canvas['scrollregion'].split()[3])
    south  = int( south*extent)
    north =  int(north*extent) + self.buttons.winfo_height() + 5
    try:
      left, top, right, bottom = canvas.bbox('current')
      if bottom > south:
        answer =  1
        k = min(5, (bottom - south) // 16)
        SCROLL_INTERVAL = si[k]
      elif top < north:
        answer = -1
        k = min(5, (north - top) // 16)
        SCROLL_INTERVAL = si[k]
    except TypeError:
      pass
    return answer
  
  def onClick(self, event):
    '''
    Respond to click on stock or waste pile.  
    Clicks on foundation piles are ignored.
    '''
    self.scrolling = False
    model = self.model
    canvas = self.tableau.canvas
    tag = [t for t in canvas.gettags('current') if t.startswith('code')][0]
    code = int(tag[4:])             # code of the card clicked
    if model.stock.find(code) != -1:
      if model.canDeal():
        self.dealUp()
        return
      else:
        self.cannotDeal()
    for k, w in enumerate(model.waste):
      idx = w.find(code)
      if idx != -1:
        break
    else:       # loop else
      return
    selection = model.grab(k, idx)
    self.grab(selection, k, event.x, event.y)
    
  def onDoubleClick(self, event):
    '''
    If the user double clicks a pile with a complete suit face up on top,
    the suit will be moved to the first available foundation pile.
    '''
    self.scrolling = False
    model = self.model
    canvas = self.tableau.canvas
    tag = [t for t in canvas.gettags('current') if t.startswith('code')][0]
    code = int(tag[4:])             # code of the card clicked
    for k, w in enumerate(model.waste):
      if [card for card in w if card.code == code]:
        break
    else:       # loop else
      return 
    if not model.completeSuit(k):
      return
    target = model.firstFoundation()
    model.grab(k, len(w)-13)
    model.selectionToFoundation(target)
    self.show()
    
  def scrollWheel(self, event):
    '''
    Use the mouse wheel to scroll the canvas.
    If we are dragging cards, they must be moved in the same direction
    as the canvas scrolls, or the cursor will become separated from the
    cards being dragged. 
    '''
    canvas = self.tableau.canvas
    lo, hi = canvas.yview()
    height = int(canvas['scrollregion'].split()[3])
    if event.num == 5 or event.delta < 0:       
      n = 1
    elif event.num == 4 or event.delta > 0:     
      n = -1
    canvas.yview_scroll(n, tk.UNITS)
    lo2, hi2 = canvas.yview()
    canvas.move('floating', 0, (hi2-hi) * height)
    
  def autoScroll(self, n):
    '''
    If scrolling has been scheduled and not canceled, scroll a bit and
    schedule some more scrolling
    '''
    if not self.scrolling:
      return
    canvas = self.tableau.canvas
    lo, hi = canvas.yview()
    height = int(canvas['scrollregion'].split()[3])
    canvas.yview_scroll(n, tk.UNITS)
    lo2, hi2 = canvas.yview()
    canvas.move('floating', 0, (hi2-hi) * height)
    canvas.after(SCROLL_INTERVAL, self.autoScroll, n)
    
  def horizontalOverlap(self, w1, e1, w2, e2):
    '''
    Find the horizontal overlap between two rectangles with west and east edges
    (w1, e1) and (w2, e2) respectively.  A negative number is returned if they
    don't overlap at all.  A return value of 0 means they coincide in one edge only.
    Vertical position of the rectangles is ignored, so they may be considered infinite
    strips.
    '''
    return min(e1, e2) - max(w1, w2)
  
  def findOverlapping(self, seq, west, east):
    '''
    Return a list of the indices of the piles in seq that overlap a card with edges west and east,
    sorted in decreasing order of overlap
    '''
    def overlap(pile):
      return self.horizontalOverlap(west, east, pile[0], pile[0]+CARDWIDTH)
    answer = [(pile, k) for k, pile in enumerate(seq) if  overlap(pile)>= 0]
    answer = sorted(answer, key = lambda x: overlap(x[0]), reverse=True)
    return [x[1] for x in answer]
   
  def onDrop(self, event):
    '''
    Drop the selected cards.  In order to recognize the destination waste pile,
    the top of the cards being dragged must be below the bottom edge of
    the foundation piles, and the cards being dragged must overlap a waste pile.
    If they overlap two waste piles, the one with more overlap is tested first.  
    If that is not a legal drop target then the other waste pile is considered.
    
    If the selection is dropped above the bottom edge of the foundation piles, 
    then we must be dragging a complete suit.
    '''
    self.scrolling = False
    model = self.model
    canvas = self.tableau.canvas   
    if not model.moving():
      return
    canvas.configure(cursor=DEFAULT_CURSOR)
    west, north, east, south = canvas.bbox(tk.CURRENT)
    success = False
     
    if north > self.foundations[0][1]+CARDHEIGHT:
      for pile in self.findOverlapping(self.waste, west, east):
        if pile == model.moveOrigin or not model.canDrop(pile):
          continue
        self.completeMove(pile)
        success = True
        break 
    elif model.movingCompleteSuit():
      #check for drop on foundation pile
      for pile in self.findOverlapping(self.foundations, west, east):
        if model.foundations[pile].isEmpty():
          self.suitToFoundation(pile)
          success = True
          break
    if not success:  
      self.abortMove()
      
    self.show()
       
  def abortMove(self):
    self.model.abortMove()
    self.tableau.canvas.yview_moveto(self.yfraction)
    self.showWaste(self.model.moveOrigin)
    self.tableau.dtag('floating', 'floating')
         
  def completeMove(self, dest):
    model = self.model
    source = model.moveOrigin
    model.selectionToWaste(dest)
    self.show()
    self.tableau.dtag('floating', 'floating')
    
  def suitToFoundation(self, dest):
    model = self.model
    source = model.moveOrigin
    model.selectionToFoundation(dest)
    self.show()
    self.tableau.dtag('floating', 'floating')    
  
  def cannotDeal(self):
    showerror('Cannot deal', "Can't deal with empty pile.")
    
  def undo(self, event):
    self.model.undo()
    self.show()
    
  def redo(self, event):
    self.model.redo()
    self.show()  
    
  def restart(self, event):
    self.model.restart()
    self.show()
    
  def redeal(self, event):
    self.model.redeal()
    self.show()
    
  def disableRedo(self):
    self.buttons.itemconfigure('redo', state=tk.HIDDEN)
  
  def disableUndo(self):
    for item in ('undo', 'restart', 'redeal'):
      self.buttons.itemconfigure(item, state=tk.HIDDEN)
    
  def enableRedo(self):
    self.buttons.itemconfigure('redo', state=tk.NORMAL)
  
  def enableUndo(self):
    for item in ('undo', 'restart', 'redeal'):
      self.buttons.itemconfigure(item, state=tk.NORMAL)
          
  def wm_delete_window(self):
      self.root.destroy()

  def done(self, num):
      self.root.destroy()    
  