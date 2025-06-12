#!/bin/bash
set -e

echo "等待MongoDB实例启动..."
sleep 10

echo "初始化副本集..."
mongo --host mongo1:27017 -u root -p example --authenticationDatabase admin <<EOF
  rs.initiate({
    _id: "rs0",
    members: [
      { _id: 0, host: "mongo1:27017", priority: 2 },
      { _id: 1, host: "mongo2:27017", priority: 1 },
      { _id: 2, host: "mongo3:27017", priority: 1 }
    ]
  });

  // 等待副本集初始化
  print("等待副本集初始化...");
  let attempts = 30;
  while(attempts > 0) {
    try {
      const status = rs.status();
      if(status.members && status.members[0].stateStr === "PRIMARY") {
        print("副本集初始化成功，主节点已选举");
        break;
      }
    } catch(err) {
      print("等待中: " + err.message);
    }
    sleep(1000);
    attempts--;
  }
EOF

echo "MongoDB副本集配置完成！"
