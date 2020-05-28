<html>
  <head>
    <title>pyramid_restler Example</title>
    <style>
      html {
        box-sizing: border-box;
        font-family: Verdana, Arial, sans-serif;
        font-size: 16px;
      }

      form {
        display: flex;
        flex-direction: row;
        align-items: center;
      }

      form > * {
        margin-right: 4px;
      }

      form > *:last-child {
        margin-right: 0;
      }

      input {
        border: 1px solid gray;
        border-radius: 2px;
        font-size: 14px;
        height: 32px;
        padding: 4px;
        width: 128px;
      }

      input[type=submit] {
        width: 64px;
      }

      table {
        border-collapse: collapse;
        border-radius: 2px;
      }

      table, th, td {
        border: 1px solid black;
      }

      th {
        font-weight: bold;
      }

      th, td {
        margin: 0;
        padding: 4px;
      }

      form {
        margin: 0;
        padding: 0;
      }
    </style>
  </head>

  <body>
    <h1>
      <a href="${request.route_url('root')}">SQLAlchemy Example</a>
    </h1>

    <h2>Collection</h2>

    <table>
      <tr>
        <th>ID</th>
        <th>Title</th>
        <th>Description</th>
        <th>GET</th>
        <th>DELETE</th>
      </tr>
      % for item in items:
        ${self.item(item)}
      % endfor
    </table>

    <p>
      <a href="${request.route_path('sqlalchemy.container.json')}">
        GET all items as JSON
      </a>
    </p>

    <h2>Add Item</h2>

    <form method="post" action="${request.route_path('sqlalchemy.container')}">
      <input type="text" name="title" placeholder="Title">
      <input type="text" name="description" placeholder="Description">
      <input type="submit" value="Add">
    </form>

    % for item in items:
      <h2>Edit Item ${item['id']}</h2>
      <form method="post" action="${request.route_path('sqlalchemy.item', id=item['id'])}">
        <input type="hidden" name="$method" value="PUT">
        <input type="text" name="title" value="${item['title']}" placeholder="Title">
        <input type="text"
               name="description"
               value="${item['description']}"
               placeholder="Description"
        >
        <input type="submit" value="Update">
      </form>
    % endfor
  </body>
</html>

<%def name="item(item)">
  <tr id="item-${item['id']}">
    <td class="item-field-id">
      ${item['id']}
    </td>
    <td class="item-field-title">
      ${item['title']}
    </td>
    <td class="item-field-description">
      ${item['description']}
    </td>
    <td>
      <a href="${request.route_path('sqlalchemy.item', id=item['id'])}"
         class="item-get-link"
      >
        ${request.route_path('sqlalchemy.item', id=item['id'])}
      </a>
    </td>
    <td>
      <form method="post"
            action="${request.route_path('sqlalchemy.item', id=item['id'])}"
            class="delete-member-form"
      >
        <input type="hidden" name="$method" value="DELETE">
        <input type="hidden"
               name="$next"
               value="${request.route_path('sqlalchemy.container')}"
        >
        <input type="submit" value="Delete">
      </form>
    </td>
  </tr>
</%def>
