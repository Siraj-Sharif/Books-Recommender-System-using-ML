from flask import Flask, render_template, request
import pickle
import numpy as np

popular_df        = pickle.load(open('popular.pkl', 'rb'))
pt                = pickle.load(open('pt.pkl', 'rb'))
books             = pickle.load(open('books.pkl', 'rb'))
similarity_scores = pickle.load(open('similarity_scores.pkl', 'rb'))

app = Flask(__name__)


@app.route('/')
def index():
    return render_template(
        'index.html',
        book_name = list(popular_df['title'].values),
        author    = list(popular_df['author'].values),
        image     = list(popular_df['image'].values),
        votes     = list(popular_df['num_ratings'].values),
        rating    = list(popular_df['avg_rating'].values)
    )


@app.route('/recommend')
def recommend_ui():
    return render_template('recommend.html')


@app.route('/recommend_books', methods=['post'])
def recommend():
    user_input = request.form.get('user_input', '').strip()

    if not user_input:
        return render_template('recommend.html', data=[], error="Please enter a book title.")

    all_titles = list(pt.index)

    # Step 1: exact match
    exact = np.where(pt.index == user_input)[0]
    if len(exact) > 0:
        return render_template('recommend.html', data=_get_recommendations(exact[0]))

    # Step 2: case-insensitive exact match
    ci = [i for i, t in enumerate(all_titles) if t.lower() == user_input.lower()]
    if ci:
        return render_template('recommend.html', data=_get_recommendations(ci[0]))

    # Step 3: all words must appear in title
    words   = user_input.lower().split()
    partial = [i for i, t in enumerate(all_titles)
               if all(w in t.lower() for w in words)]

    if len(partial) == 1:
        return render_template('recommend.html', data=_get_recommendations(partial[0]))

    if len(partial) > 1:
        suggestions = [all_titles[i] for i in partial[:10]]
        return render_template('recommend.html', data=[], suggestions=suggestions, query=user_input)

    # Step 4: any word appears in title
    substr = [i for i, t in enumerate(all_titles)
              if any(w in t.lower() for w in words if len(w) > 3)]

    if substr:
        suggestions = [all_titles[i] for i in substr[:10]]
        return render_template('recommend.html', data=[], suggestions=suggestions, query=user_input)

    # Step 5: nothing found
    return render_template(
        'recommend.html',
        data=[],
        error=f'No books found matching "{user_input}". Try keywords like "machine learning" or "thermodynamics".'
    )


def _get_recommendations(index):
    similar_items = sorted(
        list(enumerate(similarity_scores[index])),
        key=lambda x: x[1],
        reverse=True
    )[1:5]
    data = []
    for i in similar_items:
        temp_df = books[books['title'] == pt.index[i[0]]]
        deduped = temp_df.drop_duplicates('title')
        item = []
        item.extend(list(deduped['author'].values))
        item.extend(list(deduped['title'].values))
        item.extend(list(deduped['image'].values))
        data.append(item)
    return data


if __name__ == '__main__':
    app.run(debug=True)
