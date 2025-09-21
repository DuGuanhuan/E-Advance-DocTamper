
import os
import sys
import chromadb
from langchain_experimental.open_clip import OpenCLIPEmbeddings
from langchain_chroma import Chroma

def find_top3_similar(query_image_path):
    """
    在指定的图片库中，根据查询图片，找到最相似的前3张图片。

    Args:
        query_image_path (str): 用于查询的图片的路径。
    """
    photo_library_path = './photo_lib'
    db_path = "./chroma_db_photo_lib"
    collection_name = "photo_library_collection"

    # --- 1. 检查路径是否存在 ---
    if not os.path.isdir(photo_library_path):
        print(f"!!! 错误：图片库文件夹 '{photo_library_path}' 不存在。")
        print("请先创建该文件夹，并放入您的图片。")
        return

    if not os.path.exists(query_image_path):
        print(f"!!! 错误：查询图片 '{query_image_path}' 不存在。")
        return

    print("--- 开始执行图像相似度搜索 ---")

    # --- 2. 初始化模型和向量数据库 ---
    print("正在加载 CLIP 模型...")
    clip_embd = OpenCLIPEmbeddings(model_name="ViT-B-32", checkpoint="laion2b_s34b_b79k")

    # 为确保数据最新，在创建Chroma实例前，先用客户端直接删除旧集合
    try:
        print("正在清理旧的数据库索引...")
        client = chromadb.PersistentClient(path=db_path)
        client.delete_collection(name=collection_name)
        print("旧索引清理完毕。")
    except ValueError:
        print("旧索引不存在，将创建新索引。")
    except Exception as e:
        print(f"清理旧索引时发生未知错误: {e}")

    print("正在初始化向量数据库...")
    vector_store = Chroma(
        collection_name=collection_name,
        embedding_function=clip_embd,
        persist_directory=db_path,  # 为图片库使用独立的数据库目录
    )

    # --- 3. 加载图片库到数据库 ---
    print(f"正在从文件夹 '{photo_library_path}' 加载图片...")
    image_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp"}
    image_uris = [
        os.path.join(photo_library_path, f)
        for f in os.listdir(photo_library_path)
        if os.path.splitext(f.lower())[1] in image_extensions
    ]

    if not image_uris:
        print(f"!!! 警告：在图片库 '{photo_library_path}' 中没有找到任何图片文件。")
        return

    metadatas = [{"source": uri} for uri in image_uris]
    
    print(f"找到 {len(image_uris)} 张图片，正在为它们创建向量索引...")
    vector_store.add_images(uris=image_uris, metadatas=metadatas)
    print("索引创建完成。")

    # --- 4. 执行以图搜图 ---
    print(f"\n正在使用图片 '{query_image_path}' 进行查询...")
    query_vector = clip_embd.embed_image([query_image_path])[0]
    
    # 查找最相似的3个结果
    results = vector_store.similarity_search_by_vector_with_relevance_scores(
        embedding=query_vector,
        k=3
    )

    # --- 5. 打印搜索结果 ---
    print("\n--- Top 3 相似图片 ---")
    if not results:
        print("在图片库中没有找到相似的图片。")
    else:
        # 过滤掉查询图片本身（如果它也存在于库中且相似度极高）
        filtered_results = [res for res in results if res[0].metadata.get('source') != query_image_path or res[1] > 1e-5]

        if not filtered_results:
             print("除了查询图片本身，没有找到其他相似的图片。")

        for i, (doc, score) in enumerate(filtered_results):
            similarity = (1 - score) * 100
            print(f"- Top {i+1} -")
            print(f"  图片路径: {doc.metadata.get('source')}")
            print(f"  相似度: {similarity:.2f}%")
    print("--- 搜索结束 ---\n")

if __name__ == "__main__":
    # 通过命令行参数获取查询图片的路径
    if len(sys.argv) < 2:
        print("用法: python search_top3_similar.py <你的查询图片路径>")
        sys.exit(1)
    
    query_image = sys.argv[1]
    find_top3_similar(query_image)