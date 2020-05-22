# FAQ about the data

To understand how we collect, normalize and check the data, [access the metodology we use](https://drive.google.com/open?id=1escumcbjS8inzAKvuXOQocMcQ8ZCqbyHU5X5hFrPpn4).

## Hou to citate the COVI-19 data from Brasil.IO?

Reade the section [License and citation](https://github.com/turicas/covid19-br/blob/master/README.md#licen%C3%A7a-e-cita%C3%A7%C3%A3o) from our README.


## The state's number can be different from city's numbers?

**Yes**, because 2 reasons:

1. State Health Departments (Secretaria Estadual de Saúde (SES)) just stoped publishing the data by city and keeped only the state's total (it happened, for instance, with Sao Paulo for a few days);
2. SES published a incorrect info (sometimes it happens).


## The Brazilian Health Ministry's data are differente from Brasil.IO's data. Wich one is correct?

Sometimes, our data won't be the same as official data, because of a timeframe issue:
our data was collected from state's departments AFTER Health Ministry publish their data, so,
our date is more up-to-date. Also, sometimes, State Departments can send data direct to Health Ministry,
before make it public, so our data would be ou of date.


## I totalized the cases by city from a state and it is different from the official state total. Brasil.IO data is incorrect? How can I fix it?

**Probably, it is not wrong**. Not always a State Departments publish all the citys with confirmed cases. 
A data is added to our dataset after it is checked by our volunteers - it doesn't avoid the possibility we are wrong,
but the probability is very low.


## Some citys don't have data or don't have data for a specific period of time, how can I get the historical data?

The `caso` table include only the data from the first case confirmed/published by the State Health Department
and it hasn't data for everyday (there are some SES that doesn't publish a daily report). If you want a table
with city's data by day for the avaliable timeframe, check the `caso_full` table.


## The cityhall website from my city has an up-to-date data if compared to Brasil.IO dataste. What can I do to update the date?

We are only getting data from the States Health Departments. The collect is made manually
and it is hard to collect and check this data, because sometimes it is not possible to
automize the collect procedure, because the SES publish it in a incorrect format, not a
open and structured format. If you want to participate, ask your state's SES to publish
the data in an open and structured format.


## Where is the number of suspected or excluded cases?

Because our medotological approach, we are not collecting those data and we
are not intend to add then to Brasil.IO. Please, do not insist.


## The API is not limiting the cases number. What is the problem?

Our API has a pagination (10,000 registry for each page). You need to make a
requisiton for the linked page on `next` on the result. [Read the API documentation]
(api.md) for details.


## Why the death number from notorial offices published on Brasil.IO is different from the number on Portal da Transparência do Registro Civil (Civil Registry Transparency Portal)? 

We noticed that Portal da Transparência do Registro Civil (Civil Registry Transparency Portal)
update the data each hour and even death data from early days can change (we are working with the time of the death
and nor the time when it is registrated). Because we collect the hole dataset, we choosed not to update
this table hourly, so we won't overload the Portal server. So, it is expected that there are some inconsistencies
on the death data, mainly on more recent dates.

Another thing, because the number of deaths by COVID-19 is related to 
suspects and confirmed cases, some suspected cases can be changed to negative,
so the total could be *less* then before.