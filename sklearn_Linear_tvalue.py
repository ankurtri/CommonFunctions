def  coef_PValues(model,X_train): 
  params = np.append(model.intercept_,model.coef_)
  predictions = model.predict(X_train).reshape((-1,1))
  #print(predictions.shape)

  newX = pd.DataFrame({"Constant":np.ones(len(X_train))}).join(pd.DataFrame(X_train))
  MSE = ((np.sum((Y_train-predictions)**2))/(len(newX)-len(newX.columns))).values[0]

  # Note if you don't want to use a DataFrame replace the two lines above with
  # newX = np.append(np.ones((len(X),1)), X, axis=1)
  # MSE = (sum((y-predictions)**2))/(len(newX)-len(newX[0]))

  var_b = MSE*(np.linalg.inv(np.dot(newX.T,newX)).diagonal())
  sd_b = np.sqrt(var_b)
  ts_b = params/ sd_b

  p_values =[2*(1-stats.t.cdf(np.abs(i),(len(newX)-1))) for i in ts_b]

  sd_b = np.round(sd_b,3)
  ts_b = np.round(ts_b,3)
  p_values = np.round(p_values,3)
  params = np.round(params,4)

  paramDF = pd.DataFrame()
  paramDF["Coefficients"],paramDF["Standard Errors"],paramDF["t values"],paramDF["Probabilites"] = [params,sd_b,ts_b,p_values]

  indices = ['intercept'] + [i for i in X_train.columns]
  paramDF.index = indices
  paramDF.index.name = 'Variable'
  print(paramDF)

  paramDF.to_csv("coef_val.csv")
  return paramDF.copy()
