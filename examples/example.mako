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
    <script src="http://ajax.googleapis.com/ajax/libs/jquery/1.6.1/jquery.min.js"></script>
    <script src="http://ajax.microsoft.com/ajax/jquery.templates/beta1/jquery.tmpl.min.js"></script>
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
      <a href="/thing.json">GET collection as JSON</a>
    </p>

    <h2>Create Thing</h2>

    <form id="create-member-form" method="POST" action="/thing">
      Title: <input type="text" name="title" /><br />
      Description: <input type="text" name="description" /><br />
      <input type="submit" value="POST /thing" />
    </form>

    <h2>Edit Thing</h2>

    <form id="edit-member-form" method="POST" action="#">
      <input type="text" name="id" /> ID of Thing to edit<br />
      <input type="text" name="title" /> Title<br />
      <input type="text" name="description" /> Description<br />
      <input type="hidden" name="$method" value="PUT" />
      <input type="submit" value="PUT /thing/{ID}" />
    </form>

    <script id="thing-template" type="text/x-jquery-tmpl">
      ${self.thing(Thing(id='${id}', title='${title}', description='${description}'))}
    </script>

    <script>//<![CDATA[
      $(document).ready(function () {

        function onCreate (location) {
          $.ajax(location, {
            dataType: 'json',
            success: function (data) {
              var thing = data.results;
              var row = $('#thing-template').tmpl(thing).appendTo('#things');
              registerDeleteFormHandlers('#thing-' + thing.id);
            }
          });
        }

        function onUpdate (id, fields) {
          var tr = $('#thing-' + id);
          $.each(fields, function (i, item) {
            var name = item.name;
            if (name === 'title' || name === 'description') {
              tr.find('td.thing-field-' + name).html(item.value);
            }
          });
        }

        $('form#create-member-form').submit(function (e) {
          e.preventDefault();
          $.ajax(this.action, {
            type: 'POST',
            data: $(this).serialize(),
            context: this,
            success: function (data, status, xhr) {
              onCreate(xhr.getResponseHeader('Location'));
            }
          });
        });

        $('form#edit-member-form').submit(function (e) {
          e.preventDefault();
          var id = $(this).find('input[name=id]').first().val();
          var action = '/thing/' + id;
          var fields = $(this).serializeArray();
          $.ajax(action, {
            type: this.method,
            data: $(this).serialize(),
            success: function (data, status, xhr) {
              if (xhr.status == 204) {
                onUpdate(id, fields);
              } else if (xhr.status == 201) {
                onCreate(xhr.getResponseHeader('Location'));
              }
            }
          });
        });

        function registerDeleteFormHandlers (selector) {
          selector = selector || 'form.delete-member-form';
          $(selector).submit(function (e) {
            e.preventDefault();
            $.ajax(this.action, {
              type: this.method,
              data: $(this).serialize(),
              context: this,
              success: function () {
                $(this).closest('tr').remove();
              }
            });
          });
        }

        registerDeleteFormHandlers();
      });
    //]]</script>
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
