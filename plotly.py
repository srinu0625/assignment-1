import matplotlib.pyplot as plt

# Sample data
x = [1, 4, 20, 24, 30]
y = [2, 4, 6, 8, 10]

# Create the plot
plt.plot(x, y, label='Line', color='blue', marker='o')

# Add title and labels
plt.title("Basic Matplotlib Example")
plt.xlabel("X-axis")
plt.ylabel("Y-axis")

# Show grid
plt.grid(True)

# Show legend
plt.legend()

# Display the plot
plt.show()
