from flask import Flask,redirect,render_template,url_for,request,flash,session
from flaskext.mysql import MySQL
from werkzeug.utils import secure_filename
import os,json
from datetime import date

app = Flask(__name__)

app.secret_key = 'drishti'

mysql = MySQL()

app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = 'root'
app.config['MYSQL_DATABASE_DB'] = 'onlineshopping1'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)

def getData(sql,vals=0):
    con = mysql.connect()
    cur = con.cursor()
    if vals == 0: cur.execute(sql)
    else: cur.execute(sql,vals)
    res = cur.fetchall()
    cur.close()
    con.close()
    return res

def setData(sql,vals=0):
    con = mysql.connect()
    cur = con.cursor()
    if vals == 0: cur.execute(sql)
    else: cur.execute(sql,vals)
    con.commit()
    cur.close()
    con.close()
    res = cur.rowcount
    return res

@app.route('/getSubject',methods=['POST','GET'])
def getSubject():
    cid = request.form['cid']
    sql = "select * from subjects where cid=%s" % cid
    res = getData(sql)
    return json.dumps(res)

@app.route('/getProducts/',methods=['POST'])
def getProducts():
    data = request.form
    sq = "select * from products "
    sql = ""
    f = False
    if data['src'] != '':
        sql += "where name like '%s'" % data['src']
        f = True
    if data['cat'] != 'all':
        if f: sql += " and "
        else:
            sql += "where "
            f = True
        sql += "cid=%s" % data['cat']
    if data['brand'] != 'all':
        if f: sql += " and "
        else:
            sql += "where "
            f = True
        sql += "bid=%s" % data['brand']
    if 'role' in session:
        if session['role'] == 'shop':
            if f: sql += " and "
            else:
                sql += "where "
                f = True
            sql += "sid=%s" % session['uid']
    sql += " order by "
    if data['sort'] == 'new': sql += "pid desc"
    elif data['sort'] == 'old': sql += "pid asc"
    elif data['sort'] == 'lth': sql += 'price asc'
    elif data['sort'] == 'htl': sql += 'price desc'
    sq += sql + ' limit %s,12' % data['limit']
    res = getData(sq)
    cnt = getData("select count(*) from products "+sql)[0][0]
    res = [res,cnt]
    return json.dumps(res)

@app.route('/deleteProduct/',methods=['POST'])
def deleteProduct():
    pid = request.form['pid']
    sql = "delete from products where pid=%s" % pid
    setData(sql)
    return '1'

@app.route('/productStatusUpdate/',methods=['POST'])
def updateProductStatus():
    pid = request.form['pid']
    st = request.form['st']
    sql = "update products set status=%s where pid=%s"
    vals = (st,pid)
    setData(sql,vals)
    return '1'

@app.route('/')
def home():
    if 'uid' in session and 'role' in session:
        return redirect('/'+session['role']+'/home')
    sql = "select * from categories"
    cat = getData(sql)
    sql = "select * from brands"
    brands = getData(sql)
    sql = "select * from products order by rand() limit 11"
    ran = getData(sql)
    sql = "select * from products order by pid desc limit 5"
    products = getData(sql)
    return render_template('public/home.html',categories=cat,brands=brands,ran=ran,products=products)

@app.route('/product/details/<pid>/')
def publicProductDetails(pid):
    sql = "select p.pid,p.name,p.info,p.price,b.name,p.photo,s.name,s.address,p.cid from products p join brands b on b.bid=p.bid join shops s on s.sid=p.sid where p.pid=%s" % pid
    res = getData(sql)[0]
    sql = "select * from categories"
    cat = getData(sql)
    sql = "select pid,name,price,photo from products where cid=%s and pid!=%s and status=1 order by rand() limit 4"
    vals = (res[8],pid)
    ran = getData(sql,vals)
    return render_template('public/productDetails.html',data=res,categories=cat,ran=ran)

@app.route('/login/',methods=['POST','GET'])
def login():
    if request.method == 'POST':
        data = request.form
        sql = "select log_id,role from login where username=%s and password=%s"
        vals = (data['uname'],data['pword'])
        res = getData(sql,vals)
        if len(res):
            session['uid'] = res[0][0]
            session['role'] = res[0][1]
            return redirect('/'+res[0][1]+'/home')
        else:
            flash('Invalid login details')
    return render_template('public/login.html')

@app.route('/register',methods=['POST','GET'])
def register():
    data = ''
    if request.method == 'POST':
        data = request.form
        if data['pword'] == data['cpword']:
            sql = "select count(*) from login where username='%s'" % data['email']
            res = getData(sql)
            if res[0][0] == 0:
                sql = "select count(*) from user_details where phone='%s'" % data['phone']
                res = getData(sql)
                if res[0][0] == 0:
                    file = request.files['photo']
                    fn = os.path.basename(file.filename).split('.')
                    fn = fn[len(fn)-1]
                    sql = "select ifnull(max(log_id),0)+1 from login"
                    res = getData(sql)
                    log_id = res[0][0]
                    sql = "insert into login values(%s,%s,%s,'user')"
                    vals = (log_id,data['email'],data['pword'])
                    setData(sql,vals)   
                    fn = "%s.%s" % (log_id,fn)
                    sql = "insert into user_details values(%s,%s,%s,%s,%s,%s,%s,%s)"
                    vals = (log_id,data['fname'],data['lname'],data['address'],data['phone'],data['dob'],data['gender'],fn)
                    setData(sql,vals)
                    file.save('static/uploads/'+secure_filename(fn))
                    return redirect(url_for('login'))
                else:
                    flash('Phone Number Already Exists')
            else:
                flash('Email Already Exists')
        else:
            flash('Passwords Not Matching')
    return render_template('public/register.html',data=data)

@app.route('/shopregister',methods=['POST','GET'])
def shopRegister():
    data = ''
    if request.method == 'POST':
        data = request.form
        if data['pword'] == data['cpword']:
            sql = "select count(*) from login where username='%s'" % data['semail']
            res = getData(sql)
            if res[0][0] == 0:
                sql = "select count(*) from shops where phone='%s'" % data['sphone']
                res = getData(sql)
                if res[0][0] == 0:
                    sql = "select ifnull(max(log_id),0)+1 from login"
                    res = getData(sql)
                    log_id = res[0][0]
                    sql = "insert into login values(%s,%s,%s,'shop')"
                    vals = (log_id,data['semail'],data['pword'])
                    setData(sql,vals)
                    sql = "insert into shops values(%s,%s,%s,%s)"
                    vals = (log_id,data['sname'],data['saddress'],data['sphone'])
                    setData(sql,vals)
                    return redirect(url_for('login'))
                else:
                    flash('Phone Number Already Exists')
            else:
                flash('Email Already Exists')
        else:
            flash('Passwords Not Matching')
    return render_template('public/shopregister.html',data=data)

@app.route('/search/')
def getSearchData():
    src = request.args.get('search')
    sql = "select * from products where name like '%s' or info like '%s'" % ("%"+src+"%","%"+src+"%")
    res = getData(sql)
    if 'uid' in session and 'role' in session:
        if session['role'] == 'user':
            return render_template('user/searchResult.html',data=res)
    return render_template('public/searchResult.html',data=res)

@app.route('/admin/home')
def adminHome():
    if 'uid' not in session or 'role' not in session:
        return redirect(url_for('home'))
    sql = "select sid,name,address,phone,l.username from shops s join login l on l.log_id=s.sid"
    res = getData(sql)
    return render_template('admin/home.html',shops=res)

@app.route('/admin/categories',methods=['POST','GET'])
def adminCategories():
    msg = ''
    if request.method == 'POST':
        data  = request.form
        sql = "select count(*) from categories where category='%s'" % data['category']
        print(sql)
        res = getData(sql)
        if res[0][0] == 0:
            sql = "select ifnull(max(cid),0)+1 from categories"
            res = getData(sql)
            cid = res[0][0]
            sql = "insert into categories values(%s,%s)"
            vals = (cid,data['category'])
            setData(sql,vals)
        else:
            msg = "Category Already exist"
    sql = "select * from categories"
    res = getData(sql)
    return render_template('admin/categories.html',msg=msg,categories=res   )

@app.route('/deleteCategory/<cid>/')
def deleteCategory(cid):
    msg = ''
    sql = "select count(*) from products where cid=%s" % cid
    res = getData(sql)
    if res[0][0] == 0:
        sql = "delete from categories where cid=%s" % cid
        setData(sql)
    else:
        flash("Category Used in Product and cannot delete")
    return redirect(url_for('adminCategories'))
@app.route('/admin/brands',methods=['POST','GET'])
def adminBrands():
    msg = ''
    if request.method == 'POST':
        data  = request.form
        sql = "select count(*) from brands where name='%s'" % data['brand']
        print(sql)
        res = getData(sql)
        if res[0][0] == 0:
            sql = "select ifnull(max(bid),0)+1 from brands"
            res = getData(sql)
            cid = res[0][0]
            sql = "insert into brands values(%s,%s)"
            vals = (cid,data['brand'])
            setData(sql,vals)
        else:
            msg = "Brand Already exist"
    sql = "select * from brands"
    res = getData(sql)
    return render_template('admin/brands.html',msg=msg,brands=res)

@app.route('/deleteBrand/<bid>/')
def deleteBrand(bid):
    msg = ''
    sql = "select count(*) from products where bid=%s" % bid
    res = getData(sql)
    if res[0][0] == 0:
        sql = "delete from brands where bid=%s" % bid
        setData(sql)
    else:
        flash("Brands Used in Product and cannot delete")
    return redirect(url_for('adminBrands'))

@app.route('/admin/viewUsers')
def viewUsers():
    sql = "select uid,concat(fname,' ',lname) as name,phone from user_details"
    res = getData(sql)
    return render_template('admin/viewUsers.html',users=res)

@app.route('/admin/userDetails/<uid>/')
def viewUserDetails(uid):
    sql = "select uid,concat(fname,' ',lname) as name,address,phone,dob,gender,photo,username as email from user_details u join login l on l.log_id=u.uid where uid=%s" % uid
    res = getData(sql)
    return render_template('admin/userDetails.html',data=res[0])

@app.route('/shop/home')
def shopHome():
    sql = "select * from categories"
    cat = getData(sql)
    sql = "select * from brands"
    brands = getData(sql)
    return render_template('shop/home.html',categories=cat,brands=brands)

@app.route('/shop/product/add/',methods=['POST','GET'])
def addproduct():
    if request.method == 'POST':
        file = request.files['photo']
        fn = os.path.basename(file.filename).split('.')
        fn = fn[len(fn)-1]
        data = request.form
        sql = "select ifnull(max(pid),0)+1 from products"
        pid = getData(sql)[0][0]
        fn = "%s.%s" % (pid,fn)
        sql = "insert into products values(%s,%s,%s,%s,%s,%s,%s,1,%s)"
        vals = (pid,data['name'],data['info'],data['price'],data['bid'],fn,data['cid'],session['uid'])
        setData(sql,vals)
        file.save('static/uploads/products/'+secure_filename(fn))
        return redirect(url_for('shopHome'))
    sql = "select * from categories"
    cat = getData(sql)
    sql = "select * from brands"
    brands = getData(sql)
    return render_template('shop/addProduct.html',categories=cat,brands=brands)

@app.route('/shop/product/details/<pid>/',methods=['POST','GET'])
def shopProductDetails(pid):
    if request.method == 'POST':
        data = request.form
        sql = "update products set name=%s,info=%s,price=%s,bid=%s,cid=%s where pid=%s"
        vals = (data['name'],data['info'],data['price'],data['bid'],data['cid'],pid)
        setData(sql,vals)
    sql = "select * from products where pid=%s" % pid
    res = getData(sql)
    sql = "select * from categories"
    cat = getData(sql)
    sql = "select * from brands"
    brands = getData(sql)
    return render_template('shop/productDetails.html',categories=cat,brands=brands,product=res[0])

@app.route('/shop/product/updateImage/<pid>/',methods=['POST'])
def changeProductImage(pid):
    file = request.files['photo']
    fn = os.path.basename(file.filename).split('.')
    fn = fn[len(fn)-1]
    fn = "%s.%s" % (pid,fn)
    sql = "update products set photo=%s where pid=%s"
    vals = (fn,pid)
    setData(sql,vals)
    file.save('static/uploads/products/'+secure_filename(fn))
    return redirect(url_for('shopProductDetails',pid=pid))

@app.route('/shop/orders/<o_type>/')
def shopOrders(o_type):
    status = ''
    if o_type == 'pending': status = 1
    elif o_type == 'processed' : status = 2
    elif o_type == 'shipped' : status = 3
    elif o_type == 'completed' : status = 4

    sql = "select ci.ci_id,date,p.name,p.photo,p.price,ci.quantity,ci.quantity * p.price from orders o join cart c on c.cart_id=o.cart_id join cart_items ci on ci.cid=c.cart_id join products p on p.pid=ci.pid where p.sid=%s and c.status=%s"
    vals = (session['uid'],status)
    res = getData(sql,vals)
    return render_template('shop/orders.html',data=res)

@app.route('/shop/orders/details/<ci_id>/')
def shopOrderDetails(ci_id):
    sql = "select c.cart_id,date,p.name,p.info,p.photo,p.price,ci.quantity,ci.quantity * p.price,c.status,concat(o.fname,' ',o.lname),o.email,o.phone,o.address,o.city,o.state,o.pin_code from orders o join cart c on c.cart_id=o.cart_id join cart_items ci on ci.cid=c.cart_id join products p on p.pid=ci.pid where ci.ci_id=%s" % ci_id
    res = getData(sql)
    return render_template('shop/orderDetails.html',data=res[0])

@app.route('/shop/order/changeStaus/<st>/<cid>/')
def shopOrderProcess(st,cid):
    sql = "update cart set status=%s where cart_id=%s"
    vals = (st,cid)
    setData(sql,vals)
    otype = 's'
    st = int(st)
    if st == 1: otype = 'pending'
    elif st == 2: otype = 'processed'
    elif st == 3: otype = 'shipped'
    elif st == 4: otype = 'completed'
    return redirect('/shop/orders/%s/' % otype)

@app.route('/shop/salesReport/')
def shopSalesReport():
    return render_template('shop/salesReport.html')

@app.route('/shop/getSalesReportData/',methods=['POST'])
def salesReportData():
    sql = "select date_format(date,'%s') as date,p.name,p.price,ci.quantity,ci.quantity * p.price from orders o join cart c on c.cart_id=o.cart_id join cart_items ci on ci.cid=c.cart_id join products p on p.pid=ci.pid where p.sid=%s and c.status=4" % ("%Y-%m-%d",session['uid'])
    res = getData(sql)
    return json.dumps(res)

@app.route('/user/home')
def userHome():
    sql = "select * from categories"
    cat = getData(sql)
    sql = "select * from brands"
    brands = getData(sql)
    sql = "select * from products order by rand() limit 11"
    ran = getData(sql)
    sql = "select * from products order by pid desc limit 5"
    products = getData(sql)
    return render_template('user/home.html',categories=cat,brands=brands,ran=ran,products=products)

@app.route('/user/product/addToCart/',methods=['POST'])
def addToCart():
    sql = "select cart_id from cart where uid=%s and status=0" % session['uid']
    cid = ''
    res = getData(sql)
    if len(res): cid = res[0][0]
    else:
        sql = "select ifnull(max(cart_id),0)+1 from cart"
        cid = getData(sql)
        sql = "insert into cart values(%s,%s,0)"
        vals = (cid,session['uid'])
        setData(sql,vals)
    sql = "select ifnull(max(ci_id),0)+1 from cart_items"
    ci_id = getData(sql)[0][0]
    sql = "insert into cart_items values(%s,%s,%s,1)"
    vals = (ci_id,cid,request.form['pid'])
    setData(sql,vals)
    return '1'

@app.route('/user/product/addToFav/',methods=['POST'])
def addToFav():
    pid = request.form['pid']
    sql = "select count(*) from favorites where uid=%s and pid=%s"
    vals = (session['uid'],pid)
    res = getData(sql,vals)
    r = ''
    if res[0][0] == 0:
        sql = "select ifnull(max(fid),0)+1 from favorites"
        fid = getData(sql)[0][0]
        sql = "insert into favorites values(%s,%s,%s)"
        vals = (fid,session['uid'],pid)
        setData(sql,vals)
        r = '1'
    return r

@app.route('/user/cart')
def userCart():
    sql = "select cart_id,ci_id,quantity,name,price,photo from cart c join cart_items ci on ci.cid=c.cart_id join products p on p.pid=ci.pid where c.status=0 and c.uid=%s" % session['uid']
    res = getData(sql)
    return render_template('user/cart.html',cart=res)

@app.route('/user/cart/remove/',methods=['POST'])
def removeCart():
    ci_id = request.form['ci_id']
    sql = "delete from cart_items where ci_id=%s" % ci_id
    setData(sql)
    return '1'

@app.route('/user/product/removeFav/',methods=['POST'])
def removeFav():
    fid = request.form['fid']
    sql = "delete from favorites where fid=%s" % fid
    setData(sql)
    return '1'

@app.route('/user/cart/updateQty/',methods=['POST'])
def updateQty():
    data = request.form
    sql = "update cart_items set quantity=%s where ci_id=%s"
    vals = (data['qty'],data['ci_id'])
    setData(sql,vals)
    return '1'

@app.route('/user/checkout/',methods=['POST','GET'])
def userCheckout():
    if request.method == 'POST':
        data = request.form
        sql = "select ifnull(max(oid),0)+1 from orders"
        oid = getData(sql)[0][0]
        sql = "select cart_id from cart where status=0 and uid=%s" % session['uid']
        cid = getData(sql)[0][0]
        sql = "insert into orders values(%s,%s,current_date,%s,%s,%s,%s,%s,%s,%s,%s)"
        vals = (oid,cid,data['fname'],data['lname'],data['email'],data['phone'],data['address'],data['city'],data['state'],data['pin'])
        setData(sql,vals)
        sql = "update cart set status=1 where cart_id=%s" % cid
        setData(sql)
        return render_template('user/thankYou.html')
    return render_template('user/checkout.html')

@app.route('/user/product/details/<pid>/')
def userProductDetails(pid):
    sql = "select p.pid,p.name,p.info,p.price,b.name,p.photo,s.name,s.address,p.cid from products p join brands b on b.bid=p.bid join shops s on s.sid=p.sid where p.pid=%s" % pid
    res = getData(sql)[0]
    sql = "select * from categories"
    cat = getData(sql)
    sql = "select pid,name,price,photo from products where cid=%s and pid!=%s and status=1 order by rand() limit 4"
    vals = (res[8],pid)
    ran = getData(sql,vals)
    return render_template('user/productDetails.html',data=res,categories=cat,ran=ran)

@app.route('/user/products/category/<cid>/')
def userProductCategory(cid):
    sql = "select * from brands"
    br = getData(sql)
    # sql = "select pid,name,price,photo from products where status=1 and cid=%s" % cid
    # res = getData(sql)
    return render_template('public/productCategory.html',brands=br)

@app.route('/products/category/<cid>/')
def productCategory(cid):
    sql = "select * from brands"
    br = getData(sql)
    return render_template('public/productCategory.html',brands=br)

@app.route('/user/favorites')
def userFavorites():
    sql = "select fid,f.pid,p.name,p.price,p.photo from favorites f join products p on p.pid=f.pid where f.uid=%s" % session['uid']
    res = getData(sql)
    return render_template('user/favorites.html',data=res)

@app.route('/user/orders')
def userOrders():
    sql = "select ci.ci_id,date,p.name,p.photo,p.price,ci.quantity,ci.quantity * p.price from orders o join cart c on c.cart_id=o.cart_id join cart_items ci on ci.cid=c.cart_id join products p on p.pid=ci.pid where c.uid=%s" % session['uid']
    res = getData(sql)
    return render_template('user/orders.html',data=res)

@app.route('/user/orders/details/<ci_id>/')
def userOrderDetails(ci_id):
    sql = "select ci.ci_id,date,p.name,p.info,p.photo,p.price,ci.quantity,ci.quantity * p.price,c.status,concat(o.fname,' ',o.lname),o.email,o.phone,o.address,o.city,o.state,o.pin_code from orders o join cart c on c.cart_id=o.cart_id join cart_items ci on ci.cid=c.cart_id join products p on p.pid=ci.pid where ci.ci_id=%s" % ci_id
    res = getData(sql)
    return render_template('user/orderDetails.html',data=res[0])

@app.route('/user/account',methods=['POST','GET'])
def userAccount():
    if request.method == 'POST':
        data = request.form
        sql = "update user_details set fname=%s,lname=%s,address=%s,phone=%s where uid=%s"
        vals = (data['fname'],data['lname'],data['address'],data['phone'],session['uid'])
        setData(sql,vals)
        sql = "update login set username=%s where log_id=%s"
        vals = (data['email'],session['uid'])
        setData(sql,vals)
    sql = "select fname,lname,address,phone,left(dob,10),gender,photo,username from user_details u join login l on l.log_id=u.uid where u.uid=%s" % session['uid']
    res = getData(sql)
    return render_template('user/account.html',user=res[0])

@app.route('/user/account/updateImage/',methods=['POST'])
def userUpdateImage():
    file = request.files['photo']
    fn = os.path.basename(file.filename).split('.')
    fn = fn[len(fn)-1]
    uid = session['uid']
    fn = "%s.%s" % (uid,fn)
    sql = "update user_details set photo=%s where uid=%s"
    vals = (fn,uid)
    setData(sql,vals)
    file.save('static/uploads/'+secure_filename(fn))
    return redirect(url_for('userAccount'))

@app.route('/logout/')
def logout():
    del session['uid']
    del session['role']
    return redirect(url_for('home'))

app.run(debug=True)
