# 推特列表推送

需要配置一些基本的信息

```
cookies = {
    'auth_token': 'xxx',
    'ct0': 'xxx',
}
headers = {
    'authorization': 'Bearer xxx',
    'x-csrf-token': 'xxx',
}
list_id = 'xxx'
```

-   其中`list_id`为**列表的ID**，可以从列表页面的URL找到
-   `authorization`，`auth_token`，`ct0`字段，可以从如下复制出来的内容中找到

![image-20231124224101314](https://chrisyy-images.oss-cn-chengdu.aliyuncs.com/img/image-20231124224101314.png)



