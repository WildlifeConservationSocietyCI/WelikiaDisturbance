import numpy as np
import matplotlib.pyplot as plt

plt.style.use('ggplot')

flames = [np.array([1.0]), np.array([3.0]), np.array([5.0])]
ages = np.arange(start=1, stop=300, step=1)

def tree_mortality(flame, age):
        """
            Tree_mortality calculates the percentage of the canopy in a cell killed during a burning event
            This estimate is based on the age of the forest and the length of the flame
            Model logic and tree size/diameter regressions from Tim Bean
            :param: flame
            :param: age
            """
        # Convert flame length to ft
        # print flame
        flame[flame == -1] = 0
        #
        # print flame

        flame *= 3.2808399

        # print flame

        # Calculate scorch height
        scorch = (3.1817 * (flame ** 1.4503))

        # Calculate tree height
        log_age = np.ma.log(age)

        tree_height = np.where(age > 0, np.array(log_age * 44 - 93), age)
        tree_height[tree_height < 0] = 1

        # Calculate tree diameter at breast height
        dbh = np.array(25.706 * log_age - 85.383)

        dbh[age <= 35] = 5
        dbh[age <= 25] = 3
        dbh[age <= 20] = 2
        dbh[age <= 15] = 1

        # Calculate bark thickness
        bark_thickness = 0.045 * dbh

        # Define crown ratio
        crown_ratio = 0.4

        # Calculate crown height
        crown_height = tree_height * (1 - crown_ratio)

        # Calculate crown kill
        scorch_crown_height_dif = scorch - crown_height
        scorch_crown_height_dif[scorch_crown_height_dif < 0] = 0

        height_x_cr = tree_height * crown_ratio
        height_x_cr = np.ma.array(height_x_cr, mask=(height_x_cr == 0))

        crown_kill = np.where(scorch_crown_height_dif > 0,
                              np.array(41.961 * np.ma.log(
                                  100 * np.ma.divide(scorch_crown_height_dif, height_x_cr)) - 89.721),
                              0)

        crown_kill[crown_kill < 0] = 0
        crown_kill[crown_kill > 100] = 100

        # calculate percent mortality
        mortality = np.where(flame > 0,
                                np.array(
                                    1 / (1 + np.exp((-1.941 + (6.3136 * (1 - (np.exp(-1 * bark_thickness))))) - (
                                        .000535 * (crown_kill ** 2))))), flame)

        return mortality, tree_height, dbh

# print tree_mortality(flame=flame, age=age)

mortality_lists = [[], [], [], [], [], []]
tree_heights =[]
dbhs = []

for i in ages:
    f = np.array([0.5])
    x = tree_mortality(flame=f, age=i)
    print x
    mortality_lists[0].append(x[0])
    tree_heights.append(float(x[1]))
    dbhs.append(float(x[2]))

for i in ages:
    f = np.array([1.0])
    x = tree_mortality(flame=f, age=i)
    mortality_lists[1].append(x[0])

for i in ages:
    f = np.array([2.0])
    x = tree_mortality(flame=f, age=i)
    mortality_lists[2].append(x[0])

for i in ages:
    f = np.array([2.5])
    x = tree_mortality(flame=f, age=i)
    mortality_lists[3].append(x[0])


for i in ages:
    f = np.array([3.0])
    x = tree_mortality(flame=f, age=i)
    mortality_lists[4].append(x[0])

for i in ages:
    f = np.array([5.0])
    x = tree_mortality(flame=f, age=i)
    mortality_lists[5].append(x[0])



ax1 = plt.subplot(111)
ax1.plot(ages, mortality_lists[0], color='black', label='flame length $0.5 m$')
ax1.plot(ages, mortality_lists[1], color='blue', label='flame length $1.0 m$')
ax1.plot(ages, mortality_lists[2], color='red', label='flame length $2.0 m$')
ax1.plot(ages, mortality_lists[3], color='yellow', label='flame length $2.5 m$')
ax1.plot(ages, mortality_lists[4], color='green', label='flame length $3.0 m$')
ax1.plot(ages, mortality_lists[5], color='orange', label='flame length $5.0 m$')

plt.xlabel('tree age $yr$')
plt.ylabel('percent tree mortality')
plt.title('tree mortality as a function of age and flame length')
plt.legend(bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0)
plt.show()


# print tree_heights
plt.plot(ages, tree_heights)
plt.show()

plt.plot(ages, dbhs)
plt.show()

print len(ages), len(tree_heights)