import sys
import os
import glob

import numpy as np
import numpy_indexed as npi
from stl import mesh
import svgwrite

from matplotlib import pyplot
from mpl_toolkits import mplot3d

import pdb

point_accuracy = 6

def plotMesh(mesh):
  # Create a new plot
  figure = pyplot.figure()
  axes = mplot3d.Axes3D(figure)

  # Render the cube faces
  axes.add_collection3d(mplot3d.art3d.Poly3DCollection(mesh.vectors))

  # Auto scale to the mesh size
  scale = np.concatenate(mesh.points).flatten(-1)
  axes.auto_scale_xyz(scale, scale, scale)

  # Show the plot to the screen
  pyplot.show()

fileName = sys.argv[1]

if os.path.isdir(fileName):
  if(fileName[-1] is not '/'):
    fileName = fileName + '/'
  files = glob.glob(fileName + '*.stl')
  print "Found files " + str(files)
else:
  files = [fileName]

for fName in files:
  print "Running " + fName
  fileMesh = mesh.Mesh.from_file(fName)
  
  #plotMesh(fileMesh)

  #Find thinnest direction to isolate side
  allVerts = np.reshape(fileMesh.vectors,(-1,3))
  maxs = np.amax(allVerts,0)
  mins = np.amin(allVerts,0)
  widths = maxs - mins
  minDim = np.argmin(widths)

  print "Found minimum dimension with width " + str(widths[minDim])

  split = (maxs[minDim]+mins[minDim])/2

  # Drop all triangles with vertex on one side of split line
  keep = []
  for tri in fileMesh.vectors:
    if not any([x[minDim]>=split for x in tri]):
      keep.append(tri)

  keep = np.array(keep)
  fileMesh.vectors = keep

  #plotMesh(fileMesh)

  goodDir1 = (minDim+1)%3
  goodDir2 = (minDim+2)%3
  flatTriangles = keep[:,:,[goodDir1,goodDir2]]

  # Drop lines that appear in two triangles - part of interior of part
  # Sort the 2 points in each edge to ensure collision. Use 2 sort dirs to break ties
  edges = [np.array([sorted([x[0,:],x[1,:]], key=lambda v: v[0]+0.0001*v[1]),
                     sorted([x[1,:],x[2,:]], key=lambda v: v[0]+0.0001*v[1]),
                     sorted([x[2,:],x[0,:]], key=lambda v: v[0]+0.0001*v[1])]) for x in flatTriangles]
  edges = np.reshape(edges,(-1,4))
  edges,counts = npi.unique(np.around(edges,decimals=point_accuracy),return_count=True)
  edges = np.reshape(edges[counts==1,:],(-1,2,2))
  
  # Write to svg
  svg = svgwrite.Drawing(fName.split('.stl')[0]+'.svg', profile='full',size=('1000mm', '1000mm'), viewBox=('0 0 1000 1000'))
  for e in edges:
    svg.add(svg.line(tuple(e[0,:].tolist()),tuple(e[1,:].tolist()), stroke=svgwrite.rgb(0,0,0,'%')))
  svg.save()
  print "Saved " + str(edges.shape[0]) + " edges."
