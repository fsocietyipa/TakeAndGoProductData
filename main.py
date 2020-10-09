from bs4 import BeautifulSoup
from pymongo import MongoClient
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait

client = MongoClient('mongodb://localhost:27017/')


# db.getCollection('products').aggregate([
# {
# $project: {"_id": {$toString : '$_id' }, "productID": "$id", "productName": "$name", "productPrice": "$price", "productWeight": "$weight"}
# }
# ])

BASE_URL = "{SHOP_URL_HERE}"

hasNextPage = True

def saveToDb(value):
    with client:
        db = client.ParsedShopDB
        res = db["products"].update_one({"id": value["id"]}, {"$set": value}, upsert=True)
        print("Saved value to collection products", res, sep="                  ")

def getValues():
    with client:
        tmpObjList = []
        db = client.ParsedShopDB
        res = db["products"].aggregate([ { "$project": { "_id": {"$toString": '$_id'}, "productID": "$id", "productName": "$name", "productPrice": "$price", "productWeight": "$weight"}}])
        for product in res:
            tmpObj = product
            del tmpObj["_id"]
            tmpObjList.append(tmpObj)
        print(len(tmpObjList), tmpObjList)

def navigateByPage(url, pageNum):
    pageCounter = pageNum
    while hasNextPage == True:

        link = url + "&page=" + str(pageCounter) + "#/first_order"
        # if pageCounter != 1:
        #     link = url + "&page=" + str(pageCounter) + "#/"
        # else:
        #     link = url
        print(link)
        getData(link)
        pageCounter += 1


def getData(url):
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    driver = webdriver.Chrome(options=options)
    driver.get(url)
    driver.implicitly_wait(10)

    try:
        # wait for loading element to appear
        WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.XPATH, "//div[@class='list-product']")))

    except TimeoutException:
        pass
    htmlString = driver.page_source
    if driver.current_url != url:
        global hasNextPage
        hasNextPage = False
        driver.close()
    else:
        driver.close()
        soup = BeautifulSoup(htmlString, "html.parser")

        bodyList = soup.findAll("div", {"class": "list-product"})
        if len(bodyList) > 0:
            for item in bodyList:
                tmpObj = {}
                tmpObj["id"] = int(item.find("div", {"class": "product-item-text"}).find("a").get("href").split("/")[-1].split("-")[0])
                tmpObj["name"] = item.find("div", {"class": "product-item-text"}).find("a").get("title")
                tmpObj["price"] = int(item.find("div", {"class": "price"}).find("div", {"class": "mr-2"}).find("b").text.strip())
                tmpObj["weight"] = tmpObj["name"].split(" ")[-2] + " " + tmpObj["name"].split(" ")[-1]
                print(tmpObj)
                saveToDb(tmpObj)
        else:
            hasNextPage = False

# navigateByPage(BASE_URL, 1)

getValues()