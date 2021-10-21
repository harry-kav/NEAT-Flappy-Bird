import pygame
import neat
import time
import os
import random
import visualize
import graphviz

os.environ["PATH"] += os.pathsep + r'C:\Program Files\Graphviz\bin'

pygame.font.init()

#window
WIN_WIDTH = 500
WIN_HEIGHT = 720

WIN = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
pygame.display.set_caption("Flappy Bird")

#sprite lists
BIRD_SPRITES = [pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bird1.png"))), pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bird2.png"))), pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bird3.png")))]
PIPE_SPRITE = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs","pipe.png")).convert_alpha())
BASE_SPRITE = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "base.png")))
BG_SPRITE = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bg.png")))

#fonts
STAT_FONT = pygame.font.SysFont("helvetica", 50)

#keep track of generations
gen = 0

xor_inputs = []
xor_outputs = []

class Bird:
	SPRITES = BIRD_SPRITES
	MAX_ROTATION = 25
	ROTATION_VELOCITY = 20
	ANIMATION_TIME = 5

	def __init__(self, x , y):
		self.x = x
		self.y = y
		self.tilt = 0
		self.tick_count = 0
		self.vel = 0
		self.height = self.y
		self.sprite_count = 0
		self.sprite = self.SPRITES[0]

	def jump(self):
		self.vel = -10.5
		self.tick_count = 0
		self.height = self.y

	def	move(self):
		self.tick_count += 1; #a frame has passed in the game loop- acts as an indicator for time

		displacement = self.vel*self.tick_count + 0.5*(3) * (self.tick_count)**2 #displacement= velocity*time

		#if at terminal velocity displacement cannot increase
		if displacement >= 16: 
			displacement = 16

		if displacement<0: #moving up
			displacement -= 2

		self.y = self.y + displacement #change y co-ordinate based on displacement

		if displacement < 0 or self.y < self.height + 50: #tilt up if bird is in upward motion
			if self.tilt < self.MAX_ROTATION: 
				self.tilt = self.MAX_ROTATION

		else:
			if self.tilt > -90: #as the bird travels down it will tilt in a nosediving fashion until it reaches a 90 degree angle- straight down
				self.tilt -= self.ROTATION_VELOCITY

	def draw(self, win):
		self.sprite_count += 1 #tracks how many frames a sprite has been displayed for

		#animation manager- displays sprite based on current frame
		if self.sprite_count <= self.ANIMATION_TIME:
			self.sprite = self.SPRITES[0]
		elif self.sprite_count <= self.ANIMATION_TIME*2:
			self.sprite = self.SPRITES[1]
		elif self.sprite_count <= self.ANIMATION_TIME*3:
			self.sprite = self.SPRITES[2]
		elif self.sprite_count <= self.ANIMATION_TIME*4:
			self.sprite = self.SPRITES[1]
		elif self.sprite_count == self.ANIMATION_TIME*4 + 1:
			self.sprite = self.SPRITES[0]
			self.sprite_count = 0

		if self.tilt <= -80: #if the bird is nosediving switch to the appropriate sprite and stop flapping
			self.sprite = self.SPRITES[1]
			self.sprite_count = self.ANIMATION_TIME*2

		#rotate the sprite around its centre
		rotated_sprite = pygame.transform.rotate(self.sprite, self.tilt)
		new_rect = rotated_sprite.get_rect(center=self.sprite.get_rect(topleft = (self.x, self.y)).center) #finds centre
		win.blit(rotated_sprite, new_rect.topleft)

	def get_mask(self):
		return pygame.mask.from_surface(self.sprite)

#class for the pipes that act as obstacles - top and bottom pipe are included in the same object
class Pipe:
	GAP = 200 # gap between the upper and lower pipe
	VELOCITY = 8 #velocity of the pipe from right to left

	def __init__(self, x):
		self.x = x
		self.height = 0
		

		self.top = 0
		self.bottom = 0
		self.PIPE_TOP = pygame.transform.flip(PIPE_SPRITE, False, True) #flip sprite for top pipe
		self.PIPE_BOTTOM = PIPE_SPRITE

		self.passed = False #has the bird passed the pipe

		self.set_height()

	#sets the pipes to be at random heights
	def set_height(self):
		self.height = random.randrange(50, 450)
		self.top = self.height - self.PIPE_TOP.get_height() #sets the top of the pipe
		self.bottom = self.height + self.GAP

	def move(self):
		self.x -= self.VELOCITY #move the pipe to the left based on velocity

	def draw(self, win):
		win.blit(self.PIPE_TOP, (self.x, self.top))
		win.blit(self.PIPE_BOTTOM, (self.x, self.bottom))

	#pixel perfect collision as opposed to standard rectangle collision- using masks
	def collide(self, bird):
		bird_mask = bird.get_mask()
		top_mask = pygame.mask.from_surface(self.PIPE_TOP)
		bottom_mask = pygame.mask.from_surface(self.PIPE_BOTTOM)
		top_offset = (int(self.x - bird.x), int(self.top - round(bird.y)))
		bottom_offset = (int(self.x - bird.x), int(self.bottom - round(bird.y)))

		b_point = bird_mask.overlap(bottom_mask, bottom_offset)
		t_point = bird_mask.overlap(top_mask,top_offset)

		if b_point or t_point:
			return True

		return False

#base is the floor, which has an illusion of infinite scrolling
class Base:
	VELOCITY = 5
	WIDTH = BASE_SPRITE.get_width()
	SPRITE = BASE_SPRITE

	def __init__(self, y):
		self.y = y
		self.x1 = 0
		self.x2 = self.WIDTH

	#movement- two images used for base- the images are back to back and move to the left- when the first image reaches the end it moves behind, creating the illudion of infinite terrain
	def move(self):
		self.x1 -= self.VELOCITY
		self.x2 -= self.VELOCITY

		if self.x1 + self.WIDTH < 0:
			self.x1 = self.x2 +self.WIDTH

		if self.x2 + self.WIDTH < 0:
			self.x2 = self.x1 +self.WIDTH

	def draw(self, win):
		win.blit(self.SPRITE, (self.x1, self.y))
		win.blit(self.SPRITE, (self.x2, self.y))



#draws the window for the application
def draw_window(win, birds, pipes, base, score, gen):
	win.blit(BG_SPRITE, (0,-100))

	for pipe in pipes:
		pipe.draw(win)

	scoreText = STAT_FONT.render("Score: "+ str(score),1, (255,255,255))
	win.blit(scoreText, (WIN_WIDTH - 10 - scoreText.get_width(), 10)) #draw text on screen no matter how large string becomes

	genText = STAT_FONT.render("Gen: "+ str(gen),1, (255,255,255))
	win.blit(genText, (10, 10))

	aliveText = STAT_FONT.render("Alive: " + str(len(birds)),1,(255,255,255))
	win.blit(aliveText, (10, 70))

	base.draw(win)

	for bird in birds:
		bird.draw(win)

	pygame.display.update()

#main loop - this will double as a fitness function
def eval_genomes(genomes, config):
	#iterate generations
	global gen
	gen += 1
	#each position in each list corresponds to a bird - bird 0 has net 0 and ge 0 etc.
	nets = [] #neural networks
	ge = [] #genomes
	birds = []

	#create the population and their neural networks
	for _, g in genomes:
		net = neat.nn.FeedForwardNetwork.create(g, config)
		nets.append(net)
		birds.append(Bird(WIN_WIDTH/2, WIN_HEIGHT/2))
		g.fitness = 0 #fitness starts off at 0
		ge.append(g)


	base = Base(650)
	pipes = [Pipe(600)]
	win = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
	clock = pygame.time.Clock()

	score = 0

	isRunning = True #is the game running

	#game loop
	while isRunning == True:
		clock.tick(30)
		for event in pygame.event.get(): #tracks events

			#quit game
			if event.type == pygame.QUIT:
				isRunning = False
				pygame.quit()
				quit()

		
		base.move()

		#determine which pipe to check for collisions
		pipe_index = 0
		if len(birds) > 0:
			if len(pipes) > 1 and birds[0].x > pipes[0].x + pipes[0].PIPE_TOP.get_width():
				pipe_index = 1 #if the first pipe has been passed then move onto the second one
			else:
				pipe_index = 0
		else:
			isRunning = False #if there are no more birds then stop running
			break

		for x, bird in enumerate(birds):
			bird.move()
			ge[x].fitness += 0.1 #birds gain fitness for every frame that they stay alive

			#activate the neural network, giving the 3 input neurons as the bird y, the distance to the top pipe, and the distance to the bottom pipe
			output = nets[x].activate((bird.y, abs(bird.y - pipes[pipe_index].height), abs(bird.y - pipes[pipe_index].bottom)))

			xor_inputs = [bird.y, abs(bird.y - pipes[pipe_index].height), abs(bird.y - pipes[pipe_index].bottom)]

			xor_outputs = output[0]

			#birds will jump if the output neurons value is greater than 0.5 - there is only one output neuron so the index is 0
			if output[0] > 0.5:
				bird.jump()

		add_pipe = False

		remove = []

		for pipe in pipes:
			pipe.move()

			for x, bird in enumerate(birds):

				#kill bird when it collides with a pipe, and record its fitness at that moment
				if pipe.collide(bird):
					ge[x].fitness -= 1 #punish birds that hit pipes- encourage birds to go between pipes

					#remove the bird and its associated neural network and genomes
					birds.pop(x)
					nets.pop(x)
					ge.pop(x)

			#when the pipe is passed by the bird create a new pipe
			if not pipe.passed and pipe.x < bird.x:
				pipe.passed = True
				add_pipe = True 

			#if pipe is off the screen add it to the remove list
			if pipe.x + pipe.PIPE_TOP.get_width() <= 0:
				remove.append(pipe)


			

		if add_pipe:
			score += 1

			#birds that go through pipes are greatly rewarded to encourage this behaviour
			for g in ge:
				g.fitness += 5

			pipes.append(Pipe(700))

		#remove pipes in the remove list
		for r in remove:
			pipes.remove(r)

		for x, bird in enumerate(birds):

			#if the bird has hit the floor or gone above the screen
			if bird.y + bird.sprite.get_height() >= 650 or bird.y < 0:
				#remove the bird and its associated neural network and genomes

					ge[x].fitness -= 1#penalise for hitting floor or going too high

					birds.pop(x)
					nets.pop(x)
					ge.pop(x)

		#if a bird passes 50 it is likely to be perfect, so it can stop
		if score > 50:
			break

		#draw to display
		draw_window(win, birds, pipes, base, score, gen)



#run NEAT
def run(config_path):
	#configuring NEAT using the configuration file
	config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction, neat.DefaultSpeciesSet, neat.DefaultStagnation, config_path)

	#generate a new population
	population = neat.Population(config)

	#show stats
	population.add_reporter(neat.StdOutReporter(True))
	stats = neat.StatisticsReporter()
	population.add_reporter(stats)

	#generate a game based on all the genomes
	winner = population.run(eval_genomes, 50)

	#display the winning genome
	print('\nBest genome:\n{!s}'.format(winner))


	# Show output of the most fit genome against training data.
	print('\nOutput:')
	winner_net = neat.nn.FeedForwardNetwork.create(winner, config)
	for xi, xo in zip(xor_inputs, xor_outputs):
		output = winner_net.activate(xi)
		print("input {!r}, expected output {!r}, got {!r}".format(xi, xo, output))

	node_names = {-1:'A', -2: 'B', 0:'A XOR B'}
	visualize.draw_net(config, winner, True, node_names=node_names)
	visualize.plot_stats(stats, ylog=False, view=True)
	visualize.plot_species(stats, view=True)

	population = neat.Checkpointer.restore_checkpoint('neat-checkpoint-4')
	population.run(eval_genomes, 10)

#path to project directory - used to access the NEAT configuration
if __name__ == '__main__':
	local_directory = os.path.dirname(__file__)
	config_path = os.path.join(local_directory, 'config-feedForward.txt')
	run(config_path)