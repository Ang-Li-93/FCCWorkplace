import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

# Function to plot a cone
def plot_cone(ax, origin, direction, dR=0.4, length=6):  # Double the length
    u = direction / np.linalg.norm(direction)  # unit direction vector
    angle = dR  # Already in radians

    # creating the circular base of the cone
    radius = np.linspace(0, 1, 100)
    circle = np.linspace(0, 2*np.pi, 100)
    R, C = np.meshgrid(radius, circle)

    # parametric equations of the cone
    X = R * np.cos(C)
    Y = R * np.sin(C)
    Z = R / np.tan(angle)

    # rotation matrix
    a = np.array([0,0,1])
    b = u
    v = np.cross(a, b)
    s = np.linalg.norm(v)
    c = np.dot(a, b)

    I = np.eye(3)
    V = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    R = I + V + np.dot(V, V) * ((1 - c) / (s**2))

    # rotate cone to correct position
    rotated = np.dot(R, np.array([X.flatten(), Y.flatten(), Z.flatten()]))
    X = rotated[0, :].reshape(X.shape)
    Y = rotated[1, :].reshape(Y.shape)
    Z = rotated[2, :].reshape(Z.shape)

    # translate cone to origin
    X += origin[0]
    Y += origin[1]
    Z += origin[2]

    ax.plot_surface(X, Y, Z, color='b', alpha=0.3)


# Parameters for muon
muon_theta = 1.0
muon_phi = 1.5

# Convert to Cartesian coordinates
muon_direction = np.array([
    np.sin(muon_theta)*np.cos(muon_phi),
    np.sin(muon_theta)*np.sin(muon_phi),
    np.cos(muon_theta)
])

# Parameters for jet
jet_theta = 0.5
jet_phi = 1.0

# Convert to Cartesian coordinates
jet_direction = np.array([
    np.sin(jet_theta)*np.cos(jet_phi),
    np.sin(jet_theta)*np.sin(jet_phi),
    np.cos(jet_theta)
])

muon_origin = np.array([0, 0, 0])
jet_origin = np.array([0, 0, 0])

fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')

# Set the limits of the plot to ensure (0,0,0) is at the center
ax.set_xlim([-2, 2])  # Adjust as per new length
ax.set_ylim([-2, 2])  # Adjust as per new length
ax.set_zlim([0, 2])   # Adjust as per new length

# Plot muon as a point and line
ax.scatter(*muon_origin, color='r', s=100)  # Increase point size
ax.quiver(*muon_origin, *muon_direction, color='r', length=2)  # Double the length

# Plot jet as a cone and line
plot_cone(ax, jet_origin, jet_direction)
ax.quiver(*jet_origin, *jet_direction, color='b', length=2)  # Double the length

ax.set_xlabel('X')
ax.set_ylabel('Y')
ax.set_zlabel('Z')

plt.show()

# Save the plot as an image file
plt.savefig('/afs/cern.ch/work/l/lia/private/FCC/NewWorkFlow/FCCeePhysicsPerformance/case-studies/higgs/mH-recoil/3d_plot.pdf')

