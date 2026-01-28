import random
import pygame
import numpy as np


pygame.init()
clock = pygame.time.Clock()

#plant dna layout
#
#64 genes, each gene has four direction genes, then four cell type genes for that direction
#
# example, first ones are whether to grow and what gene that spot will take
# next four are what cell type it will be 32 127 0 86 2 0 2 1
#
#if its under 64 you grow
#if the cell type is 0 its another growing cell
#if its 1 then its a leaf cell
#if its 2 then its a body cell


class World:
	current_location = 0
	plantid = 1
	SCREEN_WIDTH = 1200
	SCREEN_HEIGHT = 600
	GRID_WIDTH = 200
	GRID_HEIGHT = 50
	GRID_DISPLAYED_WIDTH = SCREEN_WIDTH//10
	template = [0] * GRID_HEIGHT
	plant_grid = np.array([template.copy()]*GRID_WIDTH)
	gene_grid = plant_grid.copy()
	cell_type_grid = plant_grid.copy()
	plant_genes = {}
	boxes_to_update = []
	plant_energy = {}
	plant_life = {}
	growCellLocation = []
	starting_energy = 1000
	mutation_rate = 4
	leaf_cells = []
	sunlight_level = 20
	slow = True

class colors:
	sky_color = (50, 150, 255)
	leaf_colors = [(50, 100, 50), (0, 80, 0), (50, 150, 100)]
	stem_colors = [(80, 20, 20), (100, 20, 20), (200, 200, 0)]
	seed_colors = [(255, 0, 100), (255, 0, 40), (180, 0, 0)]

def generate_random_plant():
	plant = []
	for gene_number in range(64):
		gene = []
		for point_number in range(4):
			point = random.randrange(1, 128)
			while point == gene_number:
				point = random.randrange(1, 128)
			gene.append(point)
		for point_number in range(4):
			point = random.randrange(0, 3)
			while point == gene_number:
				point = random.randrange(0, 3)
			gene.append(point)
		plant.append(gene)

	World.plant_genes[World.plantid] = plant.copy()
	new_plant_x = random.randrange(0, World.GRID_WIDTH)
	World.plant_grid[new_plant_x, World.GRID_HEIGHT-1] = World.plantid
	World.boxes_to_update.append([new_plant_x, World.GRID_HEIGHT-1])
	World.plant_energy[World.plantid] = World.starting_energy
	World.plant_life[World.plantid] = 0
	World.plantid += 1
	World.growCellLocation.append([new_plant_x, World.GRID_HEIGHT-1])


def grow_plants():
	newGrowCellLocation = []
	for box in World.growCellLocation: # grows all the stem cells in the world

		plant_id = World.plant_grid[box[0], box[1]]
		if plant_id == 0:
			continue
		genes = World.plant_genes[plant_id] # gets the genes for the stem cell its growing

		print(World.plant_grid[box[0], box[1]]) 
		for direction in range(4): # checks each direction if it wants to grow 

			if genes[World.gene_grid[box[0], box[1]]][direction] < 64: # if the cell wants to grow

				#exceptions to not let the cell grow

				if World.plant_energy[World.plant_grid[box[0], box[1]]] < 5:   # no energy left
					continue


				new_cell_location = box.copy() # copy location and change it to where the direction defines
				if direction == 0:
					new_cell_location[0] -= 1
				elif direction == 1:
					new_cell_location[0] += 1
				elif direction == 2:
					new_cell_location[1] -= 1
				elif direction == 3:
					new_cell_location[1] += 1


				

				# exceptions to not let the cell grow

				if new_cell_location[0] == World.GRID_WIDTH:  # running off the edge of the world
					continue
				if new_cell_location[1] == World.GRID_HEIGHT:
					continue
				if new_cell_location[0] == -1:
					continue
				if new_cell_location[1] == -1:
					continue

				
				if World.plant_grid[new_cell_location[0], new_cell_location[1]] != 0:  # if theres another plant in the way
					continue


				
				World.plant_grid[new_cell_location[0], new_cell_location[1]] = World.plant_grid[box[0], box[1]]						#mark the new spot as part of the plant
				World.gene_grid[new_cell_location[0], new_cell_location[1]] = genes[World.gene_grid[box[0], box[1]]][direction]		# put the new genes in that spot

				if genes[World.gene_grid[box[0], box[1]]][direction+4] == 2:

					World.plant_energy[World.plant_grid[box[0], box[1]]] -= 1 # take energy

					World.cell_type_grid[box[0], box[1]] = 2 # the spot it left is a stem now

					World.cell_type_grid[new_cell_location[0], new_cell_location[1]] = 0 #the spot it went to is a grow cell now
					newGrowCellLocation.append([new_cell_location[0], new_cell_location[1]])

				if genes[World.gene_grid[box[0], box[1]]][direction+4] == 1:

					World.plant_energy[World.plant_grid[box[0], box[1]]] -= 2 # take energy

					World.cell_type_grid[box[0], box[1]] = 1 # the spot it left is a leaf now
					World.leaf_cells.append(new_cell_location) # adds to the leaf locations for adding energy

					World.cell_type_grid[new_cell_location[0], new_cell_location[1]] = 1 #the spot it went to is a grow cell now
					newGrowCellLocation.append([new_cell_location[0], new_cell_location[1]])

				if genes[World.gene_grid[box[0], box[1]]][direction+4] == 0:
					World.plant_energy[World.plant_grid[box[0], box[1]]] -= 5 # take energy


					World.cell_type_grid[box[0], box[1]] = 1 # the spot it left is another grow cell now.     this is the new grow cell
					newGrowCellLocation.append([new_cell_location[0], new_cell_location[1]])

					World.cell_type_grid[new_cell_location[0], new_cell_location[1]] = 1 #the spot it went to is a grow cell now  this is the old grow cell
					newGrowCellLocation.append([new_cell_location[0], new_cell_location[1]])
				
	World.growCellLocation = newGrowCellLocation.copy()
				

					

def mutate_genes(genes):
	for times in range(World.mutation_rate):
		genes[random.randrange(1, 64)][random.randrange(0, 4)] = random.randrange(1, 128)
		genes[random.randrange(1, 64)][random.randrange(4, 8)] = random.randrange(1, 3)
	return genes

def give_energy():
	for plantloc in World.leaf_cells:
		if World.plant_grid[plantloc[0], plantloc[1]] != 0:
			World.plant_energy[World.plant_grid[plantloc[0], plantloc[1]]] += World.sunlight_level

def remove_plants():
	plants_to_delete = []
	newGrowCellLocation = []
	World.leaf_cells = []
	plants_to_survive = 100
	tallest = 5
	for plantid in World.plant_life.keys():
		World.plant_life[plantid] += 1
		if World.plant_life[plantid] > World.plant_genes[plantid][0][5]*10:
			plants_to_delete.append(plantid)
	if len(plants_to_delete) > 0:
		for xloc in range(World.GRID_WIDTH):
			for yloc in range(World.GRID_HEIGHT):
				if World.plant_grid[xloc, yloc] in plants_to_delete:
					if World.cell_type_grid[xloc, yloc] == 1:
						World.leaf_cells.append([xloc, yloc])
					if World.cell_type_grid[xloc, yloc] == 2:
						if plants_to_survive > 0:
							plants_to_survive -= 1
							tallest -= 1
							new_plant_x_location = xloc-3 + random.randrange(0, 7)
							if new_plant_x_location < 0:
								new_plant_x_location = 0
							if new_plant_x_location >= World.GRID_WIDTH-1:
								new_plant_x_location = World.GRID_WIDTH-1
							if new_plant_x_location == xloc:
								continue
							genes = World.plant_genes[World.plant_grid[xloc, yloc]]

							World.plant_genes[World.plantid] = [g.copy() for g in genes]

							new_plant_x_location = random.randrange(0, World.GRID_WIDTH)
							World.plant_grid[new_plant_x_location, World.GRID_HEIGHT - 1] = World.plantid
							newGrowCellLocation.append([new_plant_x_location, World.GRID_HEIGHT - 1])
							World.plant_energy[World.plantid] = World.starting_energy
							if tallest > 0:
								World.plant_energy[World.plantid] += 100
							World.plant_life[World.plantid] = 0
							World.plantid += 1
							

					World.plant_grid[xloc, yloc] = 0
					World.cell_type_grid[xloc, yloc] = 0
					World.gene_grid[xloc, yloc] = 0
	for xloc in range(World.GRID_WIDTH):
		for yloc in range(World.GRID_HEIGHT):
			if World.cell_type_grid[xloc, yloc] == 1:
				World.leaf_cells.append([xloc, yloc])
	World.growCellLocation.extend(newGrowCellLocation)


def render_world(update_everything = True):
	if update_everything:
		for x_loc in range(World.GRID_DISPLAYED_WIDTH):
			for y_loc in range(World.GRID_HEIGHT):
				box = pygame.Surface((10, 10))
				plant_id = World.plant_grid[x_loc+World.current_location, y_loc]
				if plant_id == 0:
					color = colors.sky_color
					box.fill(color)
				else:
					if World.cell_type_grid[x_loc+World.current_location, y_loc] == 0:
						random.seed(int(plant_id))
						color = colors.stem_colors[random.randrange(0, len(colors.stem_colors))]
						box.fill(color)
					elif World.cell_type_grid[x_loc+World.current_location, y_loc] == 1:
						random.seed(int(plant_id))
						color = colors.leaf_colors[random.randrange(0, len(colors.leaf_colors))]
						box.fill(color)
					elif World.cell_type_grid[x_loc+World.current_location, y_loc] == 2:
						random.seed(int(plant_id))
						color = colors.seed_colors[random.randrange(0, len(colors.seed_colors))]
						box.fill(color)
				screen.blit(box, (x_loc*10, y_loc*10))
		random.seed()
	else:
		for loc in World.boxes_to_update:
			x_loc = loc[0]
			y_loc = loc[1]
			box = pygame.Surface((10, 10))
			plant_id = World.plant_grid[x_loc+World.current_location, y_loc]
			if plant_id == 0:
				color = colors.sky_color
				box.fill(color)
			else:
				random.seed(int(plant_id))
				color = colors.stem_colors[random.randrange(0, len(colors.stem_colors))]
				box.fill(color)
			screen.blit(box, (x_loc*10, y_loc*10))
		random.seed()

screen = pygame.display.set_mode((World.SCREEN_WIDTH, World.SCREEN_HEIGHT))

generate_random_plant()


done = False
while not done:

	grow_plants()
	give_energy()
	remove_plants()
	render_world()

	for event in pygame.event.get(): # key presses
		if event.type == pygame.QUIT:
			done = True
		if event.type == pygame.KEYDOWN:
			if event.key == pygame.K_SPACE:
				for i in range(50):
					generate_random_plant()
			if event.key == pygame.K_RIGHT:
				World.current_location += 10
				if World.current_location > World.GRID_WIDTH - World.GRID_DISPLAYED_WIDTH:
					World.current_location = 0
				render_world(True)
			if event.key == pygame.K_LEFT:
				World.current_location -= 10
				if World.current_location < 0:
					World.current_location = World.GRID_WIDTH - World.GRID_DISPLAYED_WIDTH
				render_world(True)
			if event.key == pygame.K_f:
				World.slow = not World.slow
			if event.key == pygame.K_c:
				for i in range(3):
					for xloc in range(World.GRID_WIDTH):
						World.plant_grid[xloc, World.GRID_HEIGHT-1-i] = 0
						World.cell_type_grid[xloc, World.GRID_HEIGHT - 1 - i] = 0
	if World.slow:
		clock.tick(10) #maximum frame rate
	pygame.display.flip()

