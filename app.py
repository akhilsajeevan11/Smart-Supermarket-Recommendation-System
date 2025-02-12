from flask import Flask, render_template, request, redirect,session



app = Flask(__name__)
app.secret_key="abc"




@app.route('/',methods=['GET','POST'])

def login():
    if request.method=="POST":
        username=request.form['textfield']
        password=request.form['textfield2']
        db=Db()
        qry=db.selectOne("select * from login WHERE username='"+username+"' and password='"+password+"'")
        if qry is not None:
            if qry['usertype']=='ADMIN':
                session['lg']='lin'

                return '''<script>alert('login successfully');window.location="/admin_home"</script>'''
        else:
            return '''<script>alert('user not found');window.location="/"</script>'''

    else:
       return render_template("index.html")
    

@app.route('/admin')
def admin_dashboard():
    return render_template('admin.html')




if __name__ == '__main__':
    app.run(debug=True)
