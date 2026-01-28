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
# if its 3 then it is a seed


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
	starting_energy = 50
	mutation_rate = 2
	leaf_cells = []
	sunlight_level = 3.0
	slow = True
	numPlantsPerSeed = 1

class colors:
	sky_color = (50, 150, 255)
	leaf_colors = [(50, 100, 50), (0, 80, 0), (50, 150, 100)]
	stem_colors = [(80, 20, 20), (100, 20, 20), (200, 200, 0)]
	seed_colors = [(255, 0, 100), (255, 0, 40), (180, 0, 0)]
	grow_cell_colors = [(255, 255, 255)]
	

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
			point = random.randrange(0,4)
			while point == gene_number:
				point = random.randrange(0, 4)
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

    for box in World.growCellLocation:
        x, y = box
        plant_id = World.plant_grid[x, y]
        if plant_id == 0:
            continue

        # Only grow cells can grow
        if World.cell_type_grid[x, y] != 0:
            continue

        # Energy check
        if World.plant_energy[plant_id] < 5:
            newGrowCellLocation.append(box)  # stay alive but idle
            continue

        genes = World.plant_genes[plant_id]
        gene_index = World.gene_grid[x, y]

        keep_old_tip = True  # <---- critical fix

        for direction in range(4):
            if genes[gene_index][direction] >= 64:
                continue

            nx, ny = x, y
            if direction == 0:
                nx -= 1
            elif direction == 1:
                nx += 1
            elif direction == 2:
                ny -= 1
            elif direction == 3:
                ny += 1

            nx = nx % World.GRID_WIDTH

            # Bounds check
            if nx < 0 or nx >= World.GRID_WIDTH or ny < 0 or ny >= World.GRID_HEIGHT:
                continue

            # Collision check
            if World.plant_grid[nx, ny] != 0:
                continue

            # Place new cell
            World.plant_grid[nx, ny] = plant_id
            World.gene_grid[nx, ny] = genes[gene_index][direction]

            cell_type = genes[gene_index][direction + 4]

            # ---- Cell type handling ----
            if cell_type == 2:  # stem
                World.plant_energy[plant_id] -= .5
                World.cell_type_grid[x, y] = 2
                keep_old_tip = False

            elif cell_type == 1:  # leaf
                World.plant_energy[plant_id] -= 1
                World.cell_type_grid[x, y] = 1
                World.leaf_cells.append([x, y])
                keep_old_tip = False

            elif cell_type == 3:  # seed (terminal)
                World.plant_energy[plant_id] -= 20
                World.cell_type_grid[x, y] = 3
                keep_old_tip = False

            else:  # grow -> grow
                World.plant_energy[plant_id] -= 5
                World.cell_type_grid[x, y] = 0

            # New location is always a grow tip
            World.cell_type_grid[nx, ny] = 0
            newGrowCellLocation.append([nx, ny])

            break  # only one growth per tick

        # Preserve old grow tip if it wasn't consumed
        if keep_old_tip:
            newGrowCellLocation.append(box)

    World.growCellLocation = newGrowCellLocation

def old_grow_plants():
	newGrowCellLocation = []
	for box in World.growCellLocation: # grows all the stem cells in the world
		for box in World.growCellLocation:
			keep_old_tip = True
		plant_id = World.plant_grid[box[0], box[1]]
		if plant_id == 0:
			continue
		genes = World.plant_genes[plant_id] # gets the genes for the stem cell its growing

		for direction in range(4): # checks each direction if it wants to grow 

			if genes[World.gene_grid[box[0], box[1]]][direction] < 64: # if the cell wants to grow

				#exceptions to not let the cell grow
				if World.cell_type_grid[box[0], box[1]] != 0:
					continue
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

				elif genes[World.gene_grid[box[0], box[1]]][direction+4] == 1:

					World.plant_energy[World.plant_grid[box[0], box[1]]] -= 2 # take energy

					World.cell_type_grid[box[0], box[1]] = 1 # the spot it left is a leaf now
					World.leaf_cells.append(new_cell_location) # adds to the leaf locations for adding energy

					World.cell_type_grid[new_cell_location[0], new_cell_location[1]] = 1 #the spot it went to is a grow cell now
					newGrowCellLocation.append([new_cell_location[0], new_cell_location[1]])

				elif genes[World.gene_grid[box[0], box[1]]][direction+4] == 0:
					World.plant_energy[World.plant_grid[box[0], box[1]]] -= 5 # take energy


					World.cell_type_grid[box[0], box[1]] = 0 # the spot it left is another grow cell now.     this is the new grow cell
					newGrowCellLocation.append([new_cell_location[0], new_cell_location[1]])

					World.cell_type_grid[new_cell_location[0], new_cell_location[1]] = 0 #the spot it went to is a grow cell now  this is the old grow cell
					newGrowCellLocation.append([new_cell_location[0], new_cell_location[1]])

				elif genes[World.gene_grid[box[0], box[1]]][direction+4] == 3:
					World.plant_energy[World.plant_grid[box[0], box[1]]] -= 15 # take energy


					World.cell_type_grid[box[0], box[1]] = 3 # the spot it left is a seed cell now

					World.cell_type_grid[new_cell_location[0], new_cell_location[1]] = 0 #the spot it went to is a grow cell now  this is the old grow cell
					newGrowCellLocation.append([new_cell_location[0], new_cell_location[1]])
				
	World.growCellLocation = newGrowCellLocation.copy()
				

					

def mutate_genes(genes):
	for times in range(World.mutation_rate):
		genes[random.randrange(0, 64)][random.randrange(0, 4)] = random.randrange(1, 128)
		genes[random.randrange(0, 64)][random.randrange(4, 8)] = random.randrange(1, 3)
	return genes


def give_energy_old():
    # Precompute light attenuation column by column (top-down)
    for x in range(World.GRID_WIDTH):
        light = World.sunlight_level  # start with full light at top

        for y in range(World.GRID_HEIGHT):
            cell_type = World.cell_type_grid[x, y]
            plant_id = World.plant_grid[x, y]

            if cell_type == 1 and plant_id != 0:
                # Leaf gains energy proportional to remaining light
                World.plant_energy[plant_id] += light

                # Leaves strongly reduce light for lower cells
                light *= 0.4  

            elif cell_type == 2:
                # Stems partially block light
                light *= 0.95

            elif cell_type == 0:
                # Grow cells block very little
                light *= 0.90

            # Seeds block like stems
            elif cell_type == 3:
                light *= 0.90

            # Stop early if no usable light remains
            if light < 0.01:
                break

def give_energy():
    energy_gained = {plant_id: 0 for plant_id in World.plant_energy}  # track energy from light

    for x in range(World.GRID_WIDTH):
        light = World.sunlight_level  # start with full light at top

        for y in range(World.GRID_HEIGHT):
            cell_type = World.cell_type_grid[x, y]
            plant_id = World.plant_grid[x, y]

            if plant_id != 0:
                if cell_type == 1:  # leaf
                    gained = light
                    World.plant_energy[plant_id] += gained
                    energy_gained[plant_id] += gained
                    light *= 0.4  # blocks light below
                elif cell_type == 2:  # stem
                    light *= 0.95
                elif cell_type == 0:  # grow cell
                    light *= 0.90
                elif cell_type == 3:  # seed
                    light *= 0.90

            if light < 0.01:
                break

    return energy_gained


def maintenance_cost():
	for plant_id in World.plant_energy:
		cell_count = np.count_nonzero(World.plant_grid == plant_id)
		World.plant_energy[plant_id] -= cell_count * 0.3 

def remove_plants():
	newGrowCellLocation = []
	World.leaf_cells = []

	# Gather all living plants
	living_plants = list(World.plant_life.keys())

	for plant_id in living_plants:
		# Age the plant
		World.plant_life[plant_id] += 1

		# Plant dies if energy is too low or age exceeds lifespan
		if World.plant_life[plant_id] > max(World.plant_genes[plant_id][0][5], 30): #World.plant_energy[plant_id] <= 0 
            # Remove all cells for this plant
			locs = np.argwhere(World.plant_grid == plant_id)
			for loc in locs:
				x, y = loc
				cell_type = World.cell_type_grid[x, y]
				if cell_type == 1:
					World.leaf_cells.append([x, y])  # Leaves still count for light
				# Only reproduce if seed cell AND parent has enough energy
				
				if cell_type == 3 and (World.GRID_HEIGHT - y > 2): #and World.plant_energy[plant_id] > 5:
					genes = [g.copy() for g in World.plant_genes[plant_id]]
					genes = mutate_genes(genes)
					for _ in range(World.numPlantsPerSeed):
						# Try 5 times to find an empty spot
						for attempt in range(5):
							max_distance = max(1, (World.GRID_HEIGHT - y) * 2)
							new_x = (x + random.randint(-max_distance, max_distance)) % World.GRID_WIDTH
							if World.plant_grid[new_x, World.GRID_HEIGHT - 1] == 0:
								World.plant_grid[new_x, World.GRID_HEIGHT - 1] = World.plantid
								World.growCellLocation.append([new_x, World.GRID_HEIGHT - 1])
								World.plant_genes[World.plantid] = [g.copy() for g in genes]
								World.plant_energy[World.plantid] = World.starting_energy
								World.plant_life[World.plantid] = 0
								World.plantid += 1
								break  # exit attempts once placed

                # Clear the old cell
				World.plant_grid[x, y] = 0
				World.cell_type_grid[x, y] = 0
				World.gene_grid[x, y] = 0

            # Finally, remove the plant's energy and life entries
			del World.plant_energy[plant_id]
			del World.plant_life[plant_id]
			del World.plant_genes[plant_id]

    # Rebuild leaf cells for energy calculation
	for x in range(World.GRID_WIDTH):
		for y in range(World.GRID_HEIGHT):
			if World.cell_type_grid[x, y] == 1:
				World.leaf_cells.append([x, y])

    # Update grow tips with new seeds
	World.growCellLocation.extend(newGrowCellLocation)


def old_remove_plants():
	plants_to_delete = []
	newGrowCellLocation = []
	World.leaf_cells = []
	plants_to_survive = 100
	for plantid in World.plant_life.keys():
		World.plant_life[plantid] += 1
		if World.plant_life[plantid] > World.plant_genes[plantid][0][5]*3:
			plants_to_delete.append(plantid)
	if len(plants_to_delete) > 0:
		for xloc in range(World.GRID_WIDTH):
			for yloc in range(World.GRID_HEIGHT):
				if World.plant_grid[xloc, yloc] in plants_to_delete:
					if World.cell_type_grid[xloc, yloc] == 1:
						World.leaf_cells.append([xloc, yloc])
					if World.cell_type_grid[xloc, yloc] == 3:
						if plants_to_survive > 0:
							plants_to_survive -= 1
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


def make_surface(color):
    s = pygame.Surface((10, 10))
    s.fill(color)
    return s

BOXES = {
    "sky": make_surface(colors.sky_color),
    "leaf": make_surface(colors.leaf_colors[1]),
    "stem": make_surface(colors.stem_colors[1]),
    "seed": make_surface(colors.seed_colors[1]),
	"growCell": make_surface(colors.grow_cell_colors[0])
}


def render_world(update_everything = True):
	if update_everything:
		for x_loc in range(World.GRID_DISPLAYED_WIDTH):
			for y_loc in range(World.GRID_HEIGHT):
				box = pygame.Surface((10, 10))
				plant_id = World.plant_grid[x_loc+World.current_location, y_loc]
				if plant_id == 0:
					screen.blit(BOXES["sky"], (x_loc*10, y_loc*10))
				else:
					if World.cell_type_grid[x_loc+World.current_location, y_loc] == 0:
						screen.blit(BOXES["growCell"], (x_loc*10, y_loc*10))
					elif World.cell_type_grid[x_loc+World.current_location, y_loc] == 1:
						screen.blit(BOXES["leaf"], (x_loc*10, y_loc*10))
					elif World.cell_type_grid[x_loc+World.current_location, y_loc] == 2:
						screen.blit(BOXES["stem"], (x_loc*10, y_loc*10))
					elif World.cell_type_grid[x_loc+World.current_location, y_loc] == 3:
						screen.blit(BOXES["seed"], (x_loc*10, y_loc*10))
		#random.seed()
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

def rebuild_leaf_cells():
    World.leaf_cells = []
    for x in range(World.GRID_WIDTH):
        for y in range(World.GRID_HEIGHT):
            if World.cell_type_grid[x, y] == 1:
                World.leaf_cells.append([x, y])

generate_random_plant()

tick = 0
done = False
while not done:
	tick += 1
	grow_plants()
	rebuild_leaf_cells()
	give_energy()
	maintenance_cost()
	if tick % 10 == 0:
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

