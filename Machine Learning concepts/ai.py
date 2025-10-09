import altair as alt
from vega_datasets import data

weather_data = data.seattle_weather()

# Scatter plot
scatter = (
    alt.Chart(weather_data)
    .mark_point(color='steelblue', opacity=0.6)
    .encode(
        x=alt.X('temp_max', title='Maximum Temperature (°C)'),
        y=alt.Y('temp_min', title='Minimum Temperature (°C)'),
        tooltip=['temp_max', 'temp_min', 'date']
    )
)

# Regression line
reg_line = (
    scatter.transform_regression('temp_max', 'temp_min')
    .mark_line(color='red', strokeWidth=2)
)

# Combine and style
final_plot = (scatter + reg_line).properties(
    title='Seattle Weather: Max vs Min Temperature',
    width=600,
    height=400
)

final_plot.save('output3.html')
print("✅ Plot saved successfully as output3.html")

