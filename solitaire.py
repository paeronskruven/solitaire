#!/usr/bin/env python
__author__ = 'Tommy Lundgren'

import curses
import locale
import random
import traceback


SUITS = {
    'H': u'\u2665'.encode('utf-8'),
    'S': u'\u2660'.encode('utf-8'),
    'D': u'\u2666'.encode('utf-8'),
    'C': u'\u2663'.encode('utf-8')
}

CARD_HEIGHT = 3
CARD_WIDTH = 4
FACES = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']


class Vec2(object):

    def __init__(self, x, y):
        self.x = x
        self.y = y


def draw_rect(screen, x, y, width, height, color_pair=None):
    # add lines
    screen.vline(y, x, curses.ACS_VLINE, height)
    screen.vline(y, x + width, curses.ACS_VLINE, height)
    screen.hline(y, x, curses.ACS_HLINE, width)
    screen.hline(y + height, x, curses.ACS_HLINE, width)
    # add corners
    screen.addch(y, x, curses.ACS_ULCORNER)
    screen.addch(y, x + width, curses.ACS_URCORNER)
    screen.addch(y + height, x, curses.ACS_LLCORNER)
    screen.addch(y + height, x + width, curses.ACS_LRCORNER)

    if not color_pair:
        return

    screen.attron(curses.color_pair(4))
    for y1 in range(y + 1, y + height):
        for x1 in range(x + 1, x + width):
            screen.addch(y1, x1, ' ')
    screen.attron(curses.color_pair(1))


class Card(object):

    def __init__(self, suit, face):
        self.suit = suit
        self.face = face
        self.face_up = False

    def is_red(self):
        return self.suit in ['H', 'D']


class Game(object):

    stock = None
    waste = None
    foundations = None
    tableau = None
    selection = None
    waste_selected = False
    game_won = False

    def __init__(self, screen):
        self.screen = screen
        self._new_game()

    def _new_game(self):
        self.stock = []
        self.waste = []
        self.foundations = [[] for i in xrange(0, 4)]
        self.tableau = [[] for i in xrange(0, 7)]
        self.selection = Vec2(0, 0)
        self.waste_selected = False
        self.game_won = False

        # build the deck
        for suit in ['H', 'S', 'D', 'C']:
            for face in xrange(0, 13):
                self.stock.append(Card(suit, FACES[face]))
        # shuffle the deck
        random.shuffle(self.stock)

        # create the tableau
        c_t = 0
        for i in xrange(0, 52):
            if len(self.tableau[c_t]) < c_t + 1:
                self.tableau[c_t].append(self.stock.pop(0))
            c_t = c_t + 1 if c_t < 6 else 0

        # turn the last cards of each pile
        for pile in self.tableau:
            pile[-1].face_up = True

        # face up all cards in stock (doesnt impact gameplay)
        for card in self.stock:
            card.face_up = True

    def run(self):
        should_quit = False
        while not should_quit:
            if not self.game_won:
                self._has_won()
                self.draw()
            # get input
            c = self.screen.getch()
            if c == ord('q'):
                should_quit = True
            elif c == ord('n'):
                self._new_game()

            if self.game_won:  # if game complete only allow new game or quit
                continue

            # selection
            elif c == curses.KEY_LEFT:
                self.selection.x = self.selection.x - 1 if self.selection.x > 0 else 6
                self._update_selection_y()
            elif c == curses.KEY_RIGHT:
                self.selection.x = self.selection.x + 1 if self.selection.x < 6 else 0
                self._update_selection_y()
            elif c == curses.KEY_UP:
                pile = self.tableau[self.selection.x]
                if self.selection.y - 1 < 0:
                    continue
                try:
                    if pile[self.selection.y - 1].face_up:
                        self.selection.y -= 1
                except IndexError:
                    pass
            elif c == curses.KEY_DOWN:
                pile = self.tableau[self.selection.x]
                try:
                    if pile[self.selection.y + 1].face_up:
                        self.selection.y += 1
                except IndexError:
                    pass
            # actions
            elif c == ord(' '):  # flip stock
                if len(self.stock) == 0:
                    self.stock = self.waste
                    self.waste = []
                else:
                    for i in xrange(0, 3):
                        try:
                            self.waste.append(self.stock.pop())
                        except IndexError:
                            pass
                    self.waste_selected = True
            elif c == ord('s'):  # select waste
                if self.waste_selected:
                    self.waste_selected = False
                    continue
                if len(self.waste) > 0:
                    self.waste_selected = True
            elif c == ord('f'):  # move to foundation
                self._move_to_foundation()
            # movement
            elif c == ord('1'):
                self._move_to_pile(1)
            elif c == ord('2'):
                self._move_to_pile(2)
            elif c == ord('3'):
                self._move_to_pile(3)
            elif c == ord('4'):
                self._move_to_pile(4)
            elif c == ord('5'):
                self._move_to_pile(5)
            elif c == ord('6'):
                self._move_to_pile(6)
            elif c == ord('7'):
                self._move_to_pile(7)

    def draw(self):
        self.screen.clear()
        # draw instructions
        self.screen.addstr('[N] New game, [Q] Quit')

        # draw stock
        if len(self.stock) > 0:
            draw_rect(self.screen, 1, 1, CARD_WIDTH, CARD_HEIGHT, 4)
        else:
            draw_rect(self.screen, 1, 1, CARD_WIDTH, CARD_HEIGHT)

        # draw waste
        if len(self.waste) > 0:
            if self.waste_selected:
                self.screen.attron(curses.color_pair(5))
            self._draw_card(6, 1, self.waste[-1])
        else:
            draw_rect(self.screen, 6, 1, CARD_WIDTH, CARD_HEIGHT)

        # draw foundations
        for i in xrange(0, 4):
            if len(self.foundations[i]) > 0:
                self._draw_card(i * (CARD_WIDTH + 1) + 16, 1, self.foundations[i][-1])
            else:  # no cards in this foundations yet
                draw_rect(self.screen, i * (CARD_WIDTH + 1) + 16, 1, CARD_WIDTH, CARD_HEIGHT)

        # draw tableau
        for i in xrange(0, 7):
            pile = self.tableau[i]
            if len(pile) > 0:
                for j in xrange(0, len(pile)):
                    self._draw_card(i * (CARD_WIDTH + 1) + 1, j * (CARD_HEIGHT / 2 + 1) + 5, pile[j])
            else:  # no cards in this slot
                draw_rect(self.screen, i * (CARD_WIDTH + 1) + 1, 5, CARD_WIDTH, CARD_HEIGHT)

        # draw actions
        draw_rect(self.screen, 38, 5, 21, 12)
        self.screen.addstr(6, 40, 'Move to pile')
        self.screen.addstr(7, 40, '[1 ... 7]')
        self.screen.addstr(9, 40, 'Move to foundation')
        self.screen.addstr(10, 40, '[F]')
        self.screen.addstr(12, 40, 'Flip stock')
        self.screen.addstr(13, 40, '[SPACE]')
        self.screen.addstr(15, 40, '(Un)Select waste')
        self.screen.addstr(16, 40, '[S]')

    def _draw_card(self, x, y, card):
        try:
            if not self.waste_selected and self.tableau[self.selection.x][self.selection.y] == card:
                self.screen.attron(curses.color_pair(5))
        except IndexError:
            pass
        draw_rect(self.screen, x, y, CARD_WIDTH, CARD_HEIGHT)

        if not card.face_up:
            self.screen.attron(curses.color_pair(4))
        elif card.suit in ['H', 'D']:
            self.screen.attron(curses.color_pair(2))
        else:
            self.screen.attron(curses.color_pair(3))
        # fill inside
        for y1 in range(y + 1, y + CARD_HEIGHT):
            for x1 in range(x + 1, x + CARD_WIDTH):
                self.screen.addch(y1, x1, ' ')

        if card.face_up:
            # add the suit symbol and card value
            self.screen.addstr(y + 1, x + 1, SUITS[card.suit] + card.face)

        # change back to our default color pair
        self.screen.attron(curses.color_pair(1))

    def _update_selection_y(self):
        pile = self.tableau[self.selection.x]
        for card in pile:
            if card.face_up:
                self.selection.y = pile.index(card)
                break

    def _move_to_pile(self, n):
        n -= 1
        if self.waste_selected:
            try:
                cards = self.waste[-1:]
            except IndexError:
                return
        else:
            if self.selection.x == n:  # cant move a card to its own pile
                return
            cards = self.tableau[self.selection.x][self.selection.y:]
        if len(cards) <= 0:  # something went wrong here
            return
        if cards[0].face == 'A':  # can only move aces to foundation
            return

        if cards[0].face == 'K' and len(self.tableau[n]) > 0:  # can only move kings to empty pile
            return
        elif cards[0].face != 'K':
            if len(self.tableau[n]) == 0:
                return
            new_parent_card = self.tableau[n][-1]
            # make sure the cards are not the same color
            if cards[0].is_red() == new_parent_card.is_red():
                return

            if FACES[FACES.index(cards[0].face) + 1] != new_parent_card.face:
                return

        self.tableau[n].extend(cards)

        if self.waste_selected:
            self.waste.pop()
            return
        else:
            self.tableau[self.selection.x] = self.tableau[self.selection.x][:self.selection.y]

            # face up next card if its faced down
            try:
                if not self.tableau[self.selection.x][-1].face_up:
                    self.tableau[self.selection.x][-1].face_up = True
            except IndexError:
                pass

        # update selection
        self._update_selection_y()

    def _move_to_foundation(self):
        if self.waste_selected:
            try:
                card = self.waste[-1]
            except IndexError:
                return
        else:
            if self.selection.y != len(self.tableau[self.selection.x]) - 1:  # make sure we are selecting the bottom card
                return
            card = self.tableau[self.selection.x][self.selection.y]

        # get the foundation for specific suit
        if card.suit == 'H':
            foundation = self.foundations[0]
        elif card.suit == 'S':
            foundation = self.foundations[1]
        elif card.suit == 'D':
            foundation = self.foundations[2]
        elif card.suit == 'C':
            foundation = self.foundations[3]

        try:
            if card.face == 'A' or FACES[FACES.index(card.face) - 1] == foundation[-1].face:
                foundation.append(card)
            else:
                return
        except IndexError:
            return

        if self.waste_selected:
            self.waste.pop()
        else:
            self.tableau[self.selection.x].pop()
            # face up next card if its faced down
            try:
                if not self.tableau[self.selection.x][-1].face_up:
                    self.tableau[self.selection.x][-1].face_up = True
            except IndexError:
                pass

            self._update_selection_y()

    def _has_won(self):
        i = 0
        for f in self.foundations:
            i += len(f)

        if i == 52:  # all cards are in the foundations
            self.game_won = True
            self.screen.addstr(10, 1, 'Hooray! You made it')


def main(screen):
    # remove cursor
    curses.curs_set(0)
    # setup colors
    curses.start_color()
    curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK)  # default
    curses.init_pair(2, curses.COLOR_RED, curses.COLOR_WHITE)  # red suits
    curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_WHITE)  # black suits
    curses.init_pair(4, curses.COLOR_WHITE, curses.COLOR_BLUE)  # back face
    curses.init_pair(5, curses.COLOR_WHITE, curses.COLOR_CYAN)  # selected card
    # set background color
    screen.bkgd(' ', curses.color_pair(1))

    Game(screen).run()

if __name__ == '__main__':
    locale.setlocale(locale.LC_ALL, '')
    try:
        curses.wrapper(main)
    except:
        traceback.print_exc()