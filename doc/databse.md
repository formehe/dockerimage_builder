database name:image_builder
1、若有容器，则登录容器执行建立数据库操作kubectl exec -it {pod} -n {namespace} -- mysql -u root -p
mysql commands:
    mysql -u root -p
    sudo service mysql restart
    create database image_builder
    use image_builder
    SHOW INDEX FROM table_name;

2、若有容器，进入容器登录docker login:kubectl exec -it {pod} -n {namespace} -- docker login
   email/password
initContainers:
      - name: init-db
        image: mysql:5.6
        command: ['sh', '-c', 'MYSQL_PWD=$MYSQL_ROOT_PASSWORD mysql -u root -p < /docker-entrypoint-initdb.d/init.sql']
        env:
        - name: MYSQL_ROOT_PASSWORD
          value: "123456"
        volumeMounts:
        - name: mysql-config
          mountPath: /docker-entrypoint-initdb.d