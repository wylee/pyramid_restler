<html>
  <head>
    <title>pyramid_restler Example</title>
    <style>
      table {
        border-collapse: collapse;
      }
      table, th, td {
        border: 1px solid black;
      }
      form {
        margin: 0;
        padding: 0;
      }
    </style>
  </head>

  <body>
    <h2>Things</h2>

    <table id="things">
      <tr>
        <th>ID</th>
        <th>Title</th>
        <th>Description</th>
        <th>GET</th>
        <th>DELETE</th>
     </tr>
      % for thing in things:
        ${self.thing(thing)}
      % endfor
    </table>

    <p>
      <a href="/things">GET collection as JSON</a>
    </p>

    <h2>Create Thing</h2>

    <form method="post" action="/things">
      Title: <input type="text" name="title" /><br />
      Description: <input type="text" name="description" /><br />
      <input type="submit" value="POST /thing" />
    </form>

    <h2>Edit Thing 1</h2>

    <form method="post" action="/thing/1">
      <input type="hidden" name="$method" value="PUT">
      <input type="text" name="title" /> Title<br />
      <input type="text" name="description" /> Description<br />
      <input type="submit" value="PUT /thing/1" />
    </form>
  </body>
</html>


<%def name="thing(thing)">
  <tr id="thing-${thing.id}">
    <td class="thing-field-id">${thing.id}</td>
    <td class="thing-field-title">${thing.title}</td>
    <td class="thing-field-description">${thing.description}</td>
    <td><a class="thing-get-link" href="/thing/${thing.id}">GET /thing/${thing.id}</a></td>
    <td>
      <form class="delete-member-form" method="POST" action="/thing/${thing.id}">
        <input type="hidden" name="$method" value="DELETE" />
        <input type="submit" value="DELETE /thing/${thing.id}" />
      </form>
    </td>
  </tr>
</%def>
