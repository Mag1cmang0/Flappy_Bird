# For this project we will be using pygame, random, and os as our libraries. The importing of neat and time libraries/modules are for later work
# with this project.

import pygame
import neat
import random
import time
import os
# We also need to initialize pygames fonts for the score tracker
pygame.font.init()

# First off, we begin by setting a boundary for the window that we play the game in. The dimensions are based off of the size of our background picture
WIN_WIDTH = 500
WIN_HEIGHT = 800

# Next, we load our images in. pygame.transform.scale2x is used to double the size of our images. Also, we load the bird images as a list,
# because we want to animate the bird flapping, while the other objects will not have animations other than moving across the screen
BIRD_IMGS = [pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bird1.png"))),pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bird2.png"))),pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bird3.png")))]
PIPE_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "pipe.png")))
BASE_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "base.png")))
BKG_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bg.png")))

# We also create a font size and font choice for our score
STAT_FONT = pygame.font.SysFont("msreferencesansserif", 35)

# Since we are making an object oriented game, we will create a bird class in order to allow the Neural Network to create multiple birds at once
# later on in the code
class Bird:
    # We set constants for the constraints that bound how the bird is animated including the rotational limits and rotation limits,
    # as well as how many ticks it takes to evalute(5 in this case).
    IMGS = BIRD_IMGS
    MAX_ROTATION = 25
    ROTATION_VELOCITY = 20
    ANIMATION_TIME = 5

    def __init__(self,x,y):
        self.x = x
        self.y = y
        self.tilt = 0
        self.tick_count = 0
        self.velocity = 0
        self.height = self.y
        self.img_count = 0
        self.img = self.IMGS[0]

    # Now we create a method to allow the bird to jump. Because pygame calls the top left corner of our window (0,0), we define our velocity in the 
    # negative direction so that the bird jumps upwards
    def jump(self):
        # We also reset our tick count every time we jump, because in the next method, we define the movement of the bird, and the movement is
        # dependent on a physics based equation using tick count as a time increment. Basically, when the bird jumps, we do not want to 
        # simultaneously apply a gravity to the bird during the instance that it jumps
        self.velocity = -10.5
        self.tick_count = 0
        self.height = self.y

    # Now we define the movement of the bird. Since there is no real x - direction movement, we only worry about the y-direction
    def move(self):
        #increment time element(tick) by one each time for the free-fall equation
        self.tick_count += 1 
        
        #this below is simply the equation for a physics-based parabola, with time being tick_count, and velocity being velocity
        displacement = self.velocity*self.tick_count+1.5*self.tick_count**2

        # this if statement defines "terminal velocity", if the displacement over the bird in one tick exceeds 16
        # the elif statement decrements the discplacement by 2 until it is below 0, meaning that whenever the bird is moving up during a jump,
        # it's height will be reduced by a constant of 2 until it enters the free fall as described by our physics based equation
        if displacement >= 16:
            displacement = 16
        elif displacement < 0:
            displacement -= 2

        # this just changes the y-coordinate to match how much it has been displaced
        self.y += displacement

        # This nested if statement's first part states that if the bird is traveling upwards, or the y component is less than the height + 50(50
        # is just some arbitrary value of number of pixels), to tilt the bird upwards to it's max rotation. The second part of the if statement 
        # states that if the bird is falling and it has not already rotated 90 degrees downwards, to decrement the tilt of the bird of the bird 
        # by the rotation velocity it reaches 90 degrees of rotation 
        if displacement < 0 or self.y < self.height + 50:
            if self.tilt < self.MAX_ROTATION:
                self.tilt = self.MAX_ROTATION
        else:
            if self.tilt > -90:
                self.tilt -= self.ROTATION_VELOCITY

    # Now we create a method to draw the bird 
    def draw(self, win):
        # I'm not going to explain the details, it's pretty self explanatory, but every 5 ticks the bird switches the image to the next image
        # in the sequence, and after one repetition of the animation we reset the self.img_count counter back to 0 to reset the animation
        self.img_count += 1

        if self.img_count < self.ANIMATION_TIME:
            self.img = self.IMGS[0]
        elif self.img_count < self.ANIMATION_TIME*2:
            self.img = self.IMGS[1]
        elif self.img_count < self.ANIMATION_TIME*3:
            self.img = self.IMGS[2]
        elif self.img_count < self.ANIMATION_TIME*4:
            self.img = self.IMGS[1]
        elif self.img_count < self.ANIMATION_TIME*5:
            self.img = self.IMGS[0]
            self.img_count = 0

        # This if statement just makes it so the bird isn't flapping it's wings as it falls straight down
        if self.tilt <= -80:
            self.img = self.IMGS[1]
            self.img_count = self.ANIMATION_TIME*2

        # When pygame rotates images, it rotates them round the top left corner of the image instead of around the center. This code allows it 
        # to be rotated around the center to allow for more seam-less graphics
        rotated_img = pygame.transform.rotate(self.img, self.tilt)
        new_rectangle = rotated_img.get_rect(center=self.img.get_rect(topleft = (self.x, self.y)).center)
        
        # This below code places our rotated image back in center with our initial image
        win.blit(rotated_img,new_rectangle.topleft)

    # used for collision
    def get_mask(self):
        return pygame.mask.from_surface(self.img)
    
# now lets create our second class, the pipe
class Pipe:
    # We set 2 constants, the gap between the pipes and the velocity at which the pipes move
    GAP = 200
    VEL = 5

    # Now we initialize the variables involved with the pipe class
    def __init__(self, x):
        self.x = x
        self.height = 0
        self.top = 0
        self.bottom = 0
        self.PIPE_TOP = pygame.transform.flip(PIPE_IMG, False, True)
        self.PIPE_BOTTOM = PIPE_IMG
        self.passed = False
        self.set_height()

    # We generate a random height between 50 and 450, and set the top pipe to be at that random height, and the bottom pipe to be at that height
    # plus the gap we set earlier
    def set_height(self):
        self.height = random.randrange(50,450)
        self.top = self.height - self.PIPE_TOP.get_height()
        self.bottom = self.height + self.GAP

    # move the pipe to the left constantly
    def move(self):
        self.x -= self.VEL

    #draw the pipe
    def draw(self, win):
        win.blit(self.PIPE_BOTTOM, (self.x, self.bottom))
        win.blit(self.PIPE_TOP, (self.x, self.top))

    # Now we need to detect if the pipe and the bird touch. Using our bird mask from earlier, and a mask for each pipe(top and bottom), we can 
    # figure out how the bird is interacting with the pipes
    def collide(self, bird):
        bird_mask = bird.get_mask()
        top_mask = pygame.mask.from_surface(self.PIPE_TOP)
        bottom_mask = pygame.mask.from_surface(self.PIPE_BOTTOM)

        # first, we figure out how far the bird is in the x direction, as well as the y direction from each pipe. We round the bird's y direction
        # b/c at any point the bird could be at a fraction of a y-height, and we just want integers.
        top_offset = (self.x - bird.x, self.top - round(bird.y))
        bottom_offset = (self.x - bird.x, self.bottom - round(bird.y))

        # now, we use the overlap method in order to check if the bird mask is overlapping with either the bottom or top pipe
        bottom_point = bird_mask.overlap(bottom_mask, bottom_offset)
        top_point = bird_mask.overlap(top_mask, top_offset)

        # return true if there is a collision, return false if there isn't
        if top_point or bottom_point:
            return True
        
        return False
        
# now we create our last class, the Base
class Base:
    VEL = 5
    WIDTH = BASE_IMG.get_width()
    IMG = BASE_IMG

    # for this class, in order to animate the base moving, we are going to essentially create 2 bases, one at x1, and one at x2. x2 wil always
    # exist right behind x1
    def __init__(self,y):
        self.y = y
        self.x1 = 0
        self.x2 = self.x1 + self.WIDTH

    # here we keep moving the bases to the left, and once one base is fully off the screen, we send it back to the end of the base behind it
    def move(self):
        self.x1 -= self.VEL
        self.x2 -= self.VEL

        if self.x1 + self.WIDTH < 0:
            self.x1 = self.x2 + self.WIDTH
            
        if self.x2 + self.WIDTH <0:
            self.x2 = self.x1 + self.WIDTH

    # draw the 2 bases
    def draw(self, win):
        win.blit(self.IMG, (self.x1, self.y))
        win.blit(self.IMG, (self.x2, self.y))
    
# creates a window with the background image and then calls the draw method from the bird class to place our bird with it's animations
def draw_window(win, bird, pipes, base, score):
    win.blit(BKG_IMG, (0,0))

    # We need to draw multiple pipes, so this needs to be a loop that iterates through a list of our pipes
    for pipe in pipes:
        pipe.draw(win)
    
    # draw the base
    base.draw(win)

    # draw the bird
    bird.draw(win)

    # draw the score text
    text = STAT_FONT.render("Score: " + str(score), 1,(255,255,0))
    win.blit(text, (WIN_WIDTH - 10 - text.get_width(), 10))
    
    # update the window display
    pygame.display.update()

# The function that runs the actual game
def main():
    # create a bird object at coordinates (230, 350), a base at a y coordinate of 730, and a list of pipes at 600
    base = Base(730)
    bird = Bird(230,350)
    pipes = [Pipe(600)]

    # create window
    win = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))

    # create a clock for measuring time in reference to ticks
    clock = pygame.time.Clock()

    # set score to 0 to start
    score = 0

    run = True
    # run the game
    while run:
        # 30 ticks per second
        clock.tick(30)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
   
            # this calls the jump method from the bird class every time a mouse click occurs or the space bar is pressed
            if event.type == pygame.MOUSEBUTTONDOWN:
                bird.jump()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    bird.jump()
                    
        # draw the window, with the birds, pipes, base, and the score
        draw_window(win,bird, pipes, base, score)

        # apply free fall and constant base movement
        bird.move()
        base.move()

        # this add_pipe boolean is how we will control how to constantly add pipes
        add_pipe = False

        # remove is just a list that we will use to figure out which pipes have been passed
        remove = []
        for pipe in pipes:

            # if the bird hits the pipe, quit the game
            if pipe.collide(bird):
                pygame.quit()
                quit()

            # this code adds the pipe to the remove list to be removed later on
            if pipe.x + pipe.PIPE_TOP.get_width() < 0:
                remove.append(pipe)

            # the first bit of this statement simply states that if the pipe has not been marked as passed and the pipe is 
            # behind the bird, to mark the pipe as passed. Next, it also marks the boolean: add_pipe as true
            if not pipe.passed and pipe.x < bird.x:
                pipe.passed = True
                add_pipe = True
            
            # Now we call the move method from the pipe class to shift all the pipes over
            pipe.move()

        # Because we added set add_pipe to true at the same time we set pipe_passed to true, we can use either one for this if statement condition.
        # Here, we increment the score by 1 point, and add a pipe set to the end of the list
        if add_pipe:
            score += 1
            pipes.append(Pipe(600))

        # Here, we take the pipe's index, noted in the remove array from earlier, and remove it's index from the pipes list. In practically all
        # cases this just removes the first pipe in the list, as more and more pipes get added on to the end of the list
        for rem in remove:
            pipes.remove(rem)

        # This line of code quits the game if the bird hits the ground
        if bird.y + bird.img.get_height() >= 730:
            pygame.quit()
            quit()

        # This line of code quits the game if the bird flies above the vertical limit of the window
        if bird.y + bird.img.get_height() <= -48:
            pygame.quit()
            quit()

    # Quit the game once the run loop is broken
    pygame.quit()
    quit()

# run the game
main()