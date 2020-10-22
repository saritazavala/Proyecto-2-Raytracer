#Universidad del Valle de Guatemala
#Sara Zavala 18893
#RT3
#Graficas


import math
from structFunctions import *
from utils import  *
from mathFunctions import *
from figures import *

MAX_RECURSION_DEPTH = 3


# Write a BMP file ---------------------------------
class Raytracer(object):

    # Initial values -------------------------------
    def __init__(self, filename):
      self.scene = []
      self.width = 0
      self.light = None
      self.height = 0
      self.framebuffer = []
      self.change_color = color(50, 50, 200)
      self.filename = filename
      self.x_position = 0
      self.y_position = 0
      self.ViewPort_height = 0
      self.ViewPort_width = 0
      self.glClear()

    # File Header ----------------------------------
    def header(self):
      doc = open(self.filename, 'bw')
      doc.write(char('B'))
      doc.write(char('M'))
      doc.write(dword(54 + self.width * self.height * 3))
      doc.write(dword(0))
      doc.write(dword(54))
      self.info(doc)

    # Info header ----------------------------------

    def info(self, doc):
      doc.write(dword(40))
      doc.write(dword(self.width))
      doc.write(dword(self.height))
      doc.write(word(1))
      doc.write(word(24))
      doc.write(dword(0))
      doc.write(dword(self.width * self.height * 3))
      doc.write(dword(0))
      doc.write(dword(0))
      doc.write(dword(0))
      doc.write(dword(0))

      # Image ----------------------------------
      for x in range(self.height):
        for y in range(self.width):
          doc.write(self.framebuffer[x][y].toBytes())
      doc.close()

    # Writes all the doc
    def glFinish(self):
      self.header()


# Color gl Functions ---------------------------------

    # Cleans a full image with the color defined in "change_color"
    def glClear(self):
      self.framebuffer = [[self.change_color for x in range(self.width)] for y in range(self.height)]
      self.zbuffer = [[-float('inf') for x in range(self.width)] for y in range(self.height)]


    # Draws a point according ot frameBuffer
    def glpoint(self, x, y):
      self.framebuffer[y][x] = self.change_color

    # Creates a window
    def glCreateWindow(self, width, height):
      self.width = width
      self.height = height

    # Takes a new color
    def glClearColor(self, red, blue, green):
      self.change_color = color(red, blue, green)

    # Defines the area where will be able to draw
    def glViewPort(self, x_position, y_position, ViewPort_width, ViewPort_height):
      self.x_position = x_position
      self.y_position = y_position
      self.ViewPort_height = ViewPort_height
      self.ViewPort_width = ViewPort_width

    # Compuse el vertex por que me daba error el range
    def glVertex(self, x, y):
      x_temp = round((x + 1) * (self.ViewPort_width / 2) + self.x_position)
      y_temp = round((y + 1) * (self.ViewPort_height / 2) + self.y_position)
      self.glpoint(round(x_temp), round(y_temp))

    # This function creates a Line using the glpoint() function
    def glLine(self, x1, y1, x2, y2):
      dy = abs(y2 - y1)
      dx = abs(x2 - x1)
      steep = dy > dx

      if steep:
        x1, y1 = y1, x1
        x2, y2 = y2, x2
        dy = abs(y2 - y1)
        dx = abs(x2 - x1)

      if x1 > x2:
        x1, x2 = x2, x1
        y1, y2 = y2, y1

      offset = 0
      threshold = 1
      y = y1
      for x in range(x1, x2):
        if steep:
          self.glpoint(y, x)
        else:
          self.glpoint(x, y)

        offset += dy * 2

        if offset >= threshold:
          y += 1 if y1 < y2 else -1
          threshold += 2 * dx

    def cast_ray(self, orig, direction, recursion=0):
      material, impact = self.scene_intersect(orig, direction)

      if material is None or recursion >= MAX_RECURSION_DEPTH:  # break recursion of reflections after n iterations
        return self.change_color

      offset_normal = mul(impact.normal, 1.1)

      if material.albedo[2] > 0:
        reverse_direction = mul(direction, -1)
        reflected_dir = reflect(reverse_direction, impact.normal)
        reflect_orig = sub(impact.point, offset_normal) if dot(reflected_dir, impact.normal) < 0 else sum(
          impact.point, offset_normal)
        reflected_color = self.cast_ray(reflect_orig, reflected_dir, recursion + 1)
      else:
        reflected_color = color(0, 0, 0)

      if material.albedo[3] > 0:
        refract_dir = refract(direction, impact.normal, material.refractive_index)
        refract_orig = sub(impact.point, offset_normal) if dot(refract_dir, impact.normal) < 0 else sum(
          impact.point, offset_normal)
        refract_color = self.cast_ray(refract_orig, refract_dir, recursion + 1)
      else:
        refract_color = color(0, 0, 0)



      light_dir = norm(sub(self.light.position, impact.point))
      light_distance = length(sub(self.light.position, impact.point))

      shadow_orig = sub(impact.point, offset_normal) if dot(light_dir, impact.normal) < 0 else sum(
        impact.point, offset_normal)
      shadow_material, shadow_intersect = self.scene_intersect(shadow_orig, light_dir)
      shadow_intensity = 0

      if shadow_material and length(sub(shadow_intersect.point, shadow_orig)) < light_distance:
        shadow_intensity = 0.9

      intensity = self.light.intensity * max(0, dot(light_dir, impact.normal)) * (1 - shadow_intensity)

      reflection = reflect(light_dir, impact.normal)
      specular_intensity = self.light.intensity * (
              max(0, -dot(reflection, direction)) ** material.spec
      )

      diffuse = material.diffuse * intensity * material.albedo[0]
      specular = color(255, 255, 255) * specular_intensity * material.albedo[1]
      reflection = reflected_color * material.albedo[2]
      refraction = refract_color * material.albedo[3]


      if material.texture and impact.texCoords is not None:
        text_color = material.texture.getColor(impact.texCoords[0], impact.texCoords[1])
        diffuse = text_color * 255

      return diffuse + specular + reflection + refraction



    def scene_intersect(self, orig, dir):
      zbuffer = float('inf')
      material = None
      intersect = None

      for obj in self.scene:
        hit = obj.ray_intersect(orig, dir)
        if hit is not None:
          if hit.distance < zbuffer:
            zbuffer = hit.distance
            material = obj.material
            intersect = hit

      return material, intersect

    def render(self):
      fun = int(math.pi / 2)
      for y in range(self.height):
        for x in range(self.width):
          i = (2 * (x + 0.5) / self.width - 1) * math.tan(fun / 2) * self.width / self.height
          j = (2 * (y + 0.5) / self.height - 1) * math.tan(fun / 2)
          direction = norm(V3(i, j, -1))
          self.framebuffer[y][x] = self.cast_ray(V3(0, 0, 0), direction)

#Create ---------------------------------------------------------
creeper_face = Material(texture=Texture('./Textures/holi.bmp'))
creeper = Material(texture=Texture('./Textures/block.bmp'))
creeper_feet = Material(texture=Texture('./Textures/verde.bmp'))

ivory = Material(diffuse=color(100, 100, 80), albedo=(0.6, 0.3, 0.1, 0), spec=50)
rubber = Material(diffuse=color(80, 0, 0), albedo=(0.9, 0.1, 0, 0, 0), spec=10)



leaves2 = Material(diffuse=color(157,178,75), albedo=(0.9, 0.1, 0, 0, 0),spec=10)
leaves3 = Material(diffuse=color(169,217,98), albedo=(0.9, 0.1, 0, 0, 0),spec=10)
wood = Material(diffuse=color(191,143,84), albedo=(0.6, 0.3, 0.1, 0), spec= 10)
mirror = Material(diffuse=color(255, 255, 255), albedo=(0, 10, 0.8, 0), spec=1425)
glass = Material(diffuse=color(150, 180, 200), albedo=(0, 0.5, 0.1, 0.8), spec=125, refractive_index=1.5)
white = Material(diffuse=color(255,255,255), albedo=(0.9, 0.1, 0, 0, 0), spec=10)
black = Material(diffuse=color(0, 0, 0), albedo=(0.6, 0.3, 0.1, 0), spec=50)


r = Raytracer('Proyecto_2.bmp')
r.glCreateWindow(152,152)
r.glClear()

r.light = Light(
  position=V3(-20, 20, 20),
  intensity=1.5
)

r.scene = [
  #tree -----------------------------------------------
  Cube(V3(-4.25, -1, -14), 1.25, wood),
  Cube(V3(-4.25, -1.75, -14), 1.25, wood),
  Cube(V3(-4.25, -0.5, -14), 1.25, wood),
  # #Leaves
  Cube(V3(-4.25, 0.75, -12.5), 1.25, leaves2),
  Cube(V3(-3.25, 0.75, -14), 1.25, leaves2),
  Cube(V3(-5.5, 0.75, -14), 1.25, leaves2),
  # #
  Cube(V3(-3.75, 1.75, -12.5), 1.25, leaves2),
  Cube(V3(-5, 1.75, -12.5), 1.25, leaves2),
  Cube(V3(-2.5, 1.75, -12.5), 1.25, leaves2),
  # #
  Cube(V3(-3, 2.75, -13), 1.25, leaves2),

  # # Person ---------------------------------------
  Cube(V3(0, -0.15, -6.5), 0.75, ivory),
  # # #shirt
  Cube(V3(0, -1, -6.5), 0.75, rubber),
  Cube(V3(0, -1.5, -6.5), 0.84, rubber),
  # #Left arm
  Cube(V3(-0.5, -1, -6.5), 0.5, rubber),
  # #Right arm
  Cube(V3(0.5, -1, -6.5), 0.5, rubber),
  # # #hands
  Cube(V3(-0.5, -1.3125, -6.5), 0.35, ivory),
  Cube(V3(0.5, -1.3125, -6.5), 0.35, ivory),
  #
  # #Eyes
  Cube(V3(-0.1375, -0.125, -6),0.125, white),
  Cube(V3(0.1375, -0.125, -6), 0.125, white),
  #
  #  #Pupils
  Cube(V3(-0.1375, -0.125, -5.5),0.0625, black),
  Cube(V3(0.1375, -0.125, -5.5),0.0625, black),
  # #Pants
  Cube(V3(-0.1875, -2.15, -6.5),0.4, ivory),
  Cube(V3(-0.1875, -2.5, -6.5),0.4, ivory),
  Cube(V3(0.2625, -2.15, -6.5), 0.4, ivory),
  Cube(V3(0.2625, -2.5, -6.5), 0.4, ivory),

  #Creeper -------------------------------
  Cube(V3(3.5, -0.15, -11), 1, creeper_face),
  Cube(V3(3.5, -0.85, -11), 0.75, creeper),
  Cube(V3(3.5, -1.55, -11), 0.75, creeper),
  Cube(V3(3.5, -2.25, -11), 0.75, creeper),
  #Patitas, derecha
  Cube(V3(3.85, -2.25, -10), 0.375, creeper_feet),
  Cube(V3(3.85, -2.5, -10), 0.375, creeper_feet),
  # #
  Cube(V3(3.65, -2.25, -10), 0.375, creeper_feet),
  Cube(V3(3.65, -2.5, -10), 0.375, creeper_feet),

  #Izquierda
  Cube(V3(3, -2.25, -10), 0.375, creeper_feet),
  Cube(V3(3, -2.5, -10), 0.375, creeper_feet),
  #
  Cube(V3(2.75, -2.25, -10), 0.375, creeper_feet),
  Cube(V3(2.75, -2.5, -10), 0.375, creeper_feet),

  #Dog








  #Plane(V3(0, -2.75, -10), V3(0,1, 0.001) , ivory)
]

r.render()
r.glFinish()