# Boxplot analysis

To check the variability of gs measurements we represented the measured data with Boxplot.

We used plotly library (available for Python and Javascript):
https://plotly.com/python/box-plots/

and in particular:
fig = go.Figure(data=go.Box(x=dfp[x_label], y=dfp[y_label],boxpoints="all", boxmean=True))

This method calculated outliers when they are higher than q3+1.5(q3-q1) or lower than q1-1.5(q1-q3).
Outliers is calculated based on the quartiles q1 and q3, and they are calculated with method 5 of:
R. J. Hyndman and Y. Fan, “Sample quantiles in statistical packages,” The American Statistician, 50(4), pp. 361-365, 1996.

To numericaly obtain the same results that are used in the boxplot figures we can use numpy:

```python
q1=np.quantile(datos,0.25,method='hazen')
mean=np.mean(datos)
median=np.quantile(datos,0.5,method='hazen')
q3=np.quantile(datos,0.75,method='hazen')
iq=q3-q1
for d in datos:
	test=(d>q3+1.5*iq) or (d<q1-1.5*iq)
	if test: 
		print(f'{d} is an outlier')
```

